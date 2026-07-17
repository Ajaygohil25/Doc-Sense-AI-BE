import boto3
from botocore.exceptions import NoCredentialsError, ClientError
from app.config.env_config import settings
from app.core.logging import get_logger
from app.core.s3_decorators import check_s3_availability

logger = get_logger(__name__)

class S3Service:
    def __init__(self):
        client_options = {"region_name": settings.AWS_REGION}
        if settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY:
            client_options.update({
                "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
                "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            })

        self.s3_client = boto3.client('s3', **client_options)
        self.bucket_name = settings.AWS_S3_BUCKET_NAME

    @check_s3_availability
    def upload_file(self, file_obj, object_name: str) -> bool:
        """
            Upload a file to an S3 bucket.

            :param file_obj: File-like object to upload
            :param object_name: S3 object name (Key)
            :return: True if file was uploaded, else False
        """
        try:
            # Safety: Reset a file pointer to the beginning
            if hasattr(file_obj, 'seek'):
                file_obj.seek(0)

            # validation: upload_file expects a file-like object
            if not hasattr(file_obj, "read"):
                raise TypeError(
                    "upload_file() expects a file-like object (supports .read()). "
                    "If you're trying to upload a pandas DataFrame, use upload_dataframe_as_excel()."
                )

            self.s3_client.upload_fileobj(file_obj, self.bucket_name, object_name)
            logger.info(f"File uploaded successfully to {self.bucket_name}/{object_name}")
            return True
        except (NoCredentialsError, ClientError, TypeError) as e:
            logger.exception(f"Failed to upload to s3://{self.bucket_name}/{object_name}: {e}")
            return False

    @check_s3_availability
    def upload_dataframe_as_excel(self, df, object_name: str, *, index: bool = False) -> bool:
        """
        Upload a pandas DataFrame to S3 as an Excel (.xlsx) file.

        :param df: pandas DataFrame
        :param object_name: S3 object name (Key), should typically end with .xlsx
        :param index: Whether to include the DataFrame index in the Excel output
        """
        try:
            import io

            buf = io.BytesIO()
            df.to_excel(buf, index=index)
            buf.seek(0)

            self.s3_client.upload_fileobj(buf, self.bucket_name, object_name)
            logger.info(f"DataFrame uploaded successfully to {self.bucket_name}/{object_name}")
            return True
        except Exception as e:
            logger.exception(f"Failed to upload DataFrame to s3://{self.bucket_name}/{object_name}: {e}")
            return False

    @check_s3_availability
    def download_file(self, object_name, file_path):
        """
        Download a file from S3 to local path

        :param object_name: S3 object name to download
        :param file_path: Local path to save the file
        :return: True if file was downloaded, else False
        """
        try:
            self.s3_client.download_file(self.bucket_name, object_name, file_path)
            logger.info(f"File downloaded successfully from {self.bucket_name}/{object_name} to {file_path}")
            return True
        except (NoCredentialsError, ClientError) as e:
            logger.exception(f"Failed to download s3://{self.bucket_name}/{object_name} to {file_path}: {e}")
            return False

    @check_s3_availability
    def generate_presigned_url(self, object_name, expiration=3600):
        """
        Generate a presigned URL to share an S3 object

        :param object_name: string
        :param expiration: Time in seconds for the presigned URL to remain valid
        :return: Presigned URL as string. If error, returns None.
        """
        try:
            response = self.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
            return response
        except (NoCredentialsError, ClientError) as e:
            logger.exception(f"Failed to generate presigned url for s3://{self.bucket_name}/{object_name}: {e}")
            return None

    @check_s3_availability
    def check_file_exists(self, object_name: str) -> bool:
        """
        Check if a file exists in the S3 bucket.

        :param object_name: S3 object name (Key)
        :return: True if file exists, else False
        """
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=object_name)
            return True
        except ClientError as e:
            # HeadObject returns 404 if the object is missing
            if e.response['Error']['Code'] == "404":
                return False
            raise

    @check_s3_availability
    def read_file_stream(self, object_name):
        """
        Read a file directly from S3 as a stream (useful for pandas)

        :param object_name: S3 object name
        :return: BytesIO object
        :raises ClientError: if key doesn't exist (NoSuchKey), access denied, etc.
        """
        response = self.s3_client.get_object(Bucket=self.bucket_name, Key=object_name)
        import io
        return io.BytesIO(response['Body'].read())

    def delete_file(self, object_name):
        """ Delete a file from the S3 bucket using the object name."""
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=object_name)
            logger.info(f"File deleted successfully {self.bucket_name}/{object_name}")
            return True
        except (NoCredentialsError, ClientError) as e:
            logger.exception(f"Failed to delete s3://{self.bucket_name}/{object_name}: {e}")
            return False
