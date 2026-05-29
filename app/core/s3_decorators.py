from functools import wraps

from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError, EndpointConnectionError, BotoCoreError
from app.core.logging import get_logger
from app.exceptions.exceptions import S3ServiceUnavailableError

logger = get_logger(__name__)

def check_s3_availability(func):
    """
    Decorator that catches only REAL S3 service/connectivity issues.
    Does NOT catch NoSuchKey, AccessDenied, etc. — those are application-level errors.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except EndpointConnectionError as e:
            logger.error(f"S3 endpoint connection failed: {e}")
            raise S3ServiceUnavailableError("Cannot reach Amazon S3 service. Please check your network or try again later.") from e
        except ClientError as e:
            error_code = e.response['Error']['Code']
            # These are real service-level issues
            service_error_codes = {
                'RequestTimeout',
                'ServiceUnavailable',
                'InternalError',
                'SlowDown',
                'Throttling',
                # Add more if needed: https://docs.aws.amazon.com/AmazonS3/latest/API/ErrorResponses.html
            }
            if error_code in service_error_codes or e.response['ResponseMetadata']['HTTPStatusCode'] >= 500:
                logger.error(f"S3 service-level error ({error_code}): {e}")
                raise S3ServiceUnavailableError("Amazon S3 service is temporarily unavailable. Please try again later.") from e
            else:
                # This is a client error (e.g. NoSuchKey, AccessDenied, InvalidObjectState, etc.)
                # Let it bubble up naturally — caller should handle it
                raise
        except (BotoCoreError, Boto3Error) as e:
            # Lower-level botocore/boto3 issues (e.g. config, credentials, network)
            logger.error(f"Unexpected boto3/botocore error: {e}")
            raise S3ServiceUnavailableError("Failed to communicate with Amazon S3. Please check your configuration and network.") from e
    return wrapper

