STATUS = "status"
UNEXPECTED_ERROR = "Unexpected Error Occurred in {0} due to error {1} in job id {2}"

SUCCESS_STATUS = "Success"
FAILED_STATUS = "Failed"


MESSAGE = "Message"
WELCOME_MSG = "Welcome! Turf booking mode is ON"
INCORRECT_CREDENTIALS = "Email id or password is incorrect, try again"

LOGIN_SUCCESS = "Login Successfully"
LOGIN_FAILED = "Login Failed"
OTP_MESSAGE = "OTP is : {0}"
LOGIN_CONTENT = "Thank you for logging in our system !"
LOGIN_SUB = "This is a mail for Log in system"
INVALID_PASSWORD = ("Password must be at least 8 characters long, include at least one uppercase letter, "
                    "one lowercase letter, one number, and one special character.")
INVALID_EMAIL = ("An email address must contain exactly one `@` symbol, separating the local part (user name) from the domain part (email provider or organization domain). "
                 "It should not have spaces, and special characters like periods, underscores, and hyphens are allowed but with certain restrictions.")

INVALID_CONTACT = "Invalid contact number. Please enter a 10-digit contact number."



INVALID_STRING_INPUT = "Invalid string input, should not contain any special character. Please enter a valid string input."

INVALID_AMOUNT = "Invalid amount. Please enter a valid amount."

INVALID_CREDENTIALS = "Could not validate credentials, Sing-in again ! "
INVALID_USER = "User is not active or not verified, please contact the administrator"
INVALID_FORMAT = "Invalid format of email or password"
DETAILS = "Details"
NO_DATA_TO_UPDATE = "There is no data to update"
ERROR_MESSAGE = "Something went wrong, please try again later ! {0}"
NOT_ALLOWED = "You are not allowed to perform this action"

USER_ALREADY_EXISTS = "User with {0} already exists"
USER_CREATED = "Account created successfully !"
USER_DELETED = "User deleted successfully !"
USER_UPDATED = "User updated successfully !"
USER_NOT_FOUND = "User not found"
USER_NOT_REGISTERED = "User with this mail id not registered"
NOT_AUTHORIZED = "Not authorized to perform this action, please Sing-in again !"
USER_ALREADY_LOGGED_IN = "User already logged in"
USER_NOT_LOGGED_IN = "User not logged in"
SING_IN = "sign-in app"

ACCESS_TOKEN = "access_token"
TOKEN_SUB = "sub"
TOKEN_USER_ID = "user_id"
BEARER = "bearer"
TOKEN_TYPE = "token_type"
PASSWORD_DOES_NOT_MATCH = "New password and confirm password do not match! Try again"
PASSWORD_CHANGED = "Password changed successfully !"
PASSWORD_SHOULD_NOT_BE_SAME = "New password and old password should not be same! Try again"
EXPIRES = "exp"
IS_REFRESH = "is_refresh"

FORGOT_PASSWORD_SUB = "Reset your password"
EMAIL_SENT = "Email has been sent for password reset"
WWW_AUTHENTICATE = "WWW-Authenticate"
NEW_PASSWORD_NOT_SAME = "New password and confirm password do not match! Try again."
LOGOUT_SUCCESS = "Logout successful"
NEXT_PAGE = "next_page"
PREV_PAGE = "previous_page"
INVALID_FEEDBACK_INPUT = "Invalid feedback input data !"

INVALID_ACCESS_TOKEN = "Invalid access token !"
VALID_ACCESS_TOKEN = "Token is valid"
REFRESH_TOKEN_INVALID = "Refresh token is invalid, Please sing-in in the application."
REFRESH_TOKEN_REQUIRED = "Refresh token is required. Please provide a valid refresh token"
ACCESS_TOKEN_REQUIRED = "Access token is required. Please provide a valid access token, not refresh token"
TOKEN_EXPIRED = "This token has expired"
ID = "id"
PROMPT = "prompt"
CONSENT = "consent"
ACCESS_TYPE = "access_type"
OFFLINE = "offline"
INVALID_NAME = "Name can only contain alphabets"
INVALID_CURRENT_PASSWORD = "Current password is incorrect"
INVALID_TOKEN_OR_ALREADY_LOGOUT = "Invalid token or user has already logged out"

USER_DATA_UPDATED = "User data updated successfully !"

ROLE_TYPE = "Role"
INVALID_USER_ACTION = "Invalid user action ! This user has not a role of manager"

FORGOT_PASSWORD_CONTENT = "Thank you for requesting a password reset. Please follow the link below to reset your password."

FILE_UPLOAD_SUCCESS = "File uploaded successfully !"

HTTP_EXCEPTION_CODE = "HTTP ERROR"
VALIDATION_EXCEPTION_CODE = "VALIDATION ERROR"
INTERNAL_SERVER_ERROR_CODE = "INTERNAL SERVER ERROR"
INVALID_REQUEST_PAYLOAD = "Invalid request payload"
UNEXPECTED_ERROR_MESSAGE = "Unexpected error occurred"
TOKENS_CREATED_SUCCESSFULLY = "Tokens created successfully"

INVENTORY_ITEM = "Inventory Item"
KIT_ITEM = "Kit Item"

# Logger message constants
LOG_VALIDATE_SAVE_INVENTORY_KIT_FILE_FAILED = "Failed to validate or save the inventory kit file: %s"
LOG_VALIDATE_OR_UPLOAD_FILE_FAILED = "Failed to validate or upload file: %s"
LOG_FIND_RECONCILIATION_ERROR = "Error in find_reconciliation_service for file: %s"
LOG_AMAZON_FETCH_FAILED_RETRYING = "Amazon fetch failed for SKU %s. Retrying after %ss."
LOG_AMAZON_FETCH_FAILED_AFTER_RETRY = "Amazon fetch failed for SKU %s after retry."
LOG_UNEXPECTED_ERROR_FETCHING_AMAZON = "Unexpected error fetching Amazon data for SKU %s: %s"
LOG_EMPTY_INVENTORY_KIT_MAPPING = "Empty inventory_kit_mapping provided; nothing to process."
LOG_SKIP_INVENTORY_DUE_TO_AMAZON_FAILURE = "Skipping inventory SKU %s due to Amazon data fetch failure."
LOG_AMAZON_SNAPSHOT_STORED_INVENTORY = "Amazon snapshot stored for inventory item: %s"
LOG_KIT_DETAILS_MISSING_SKU = "Kit item details missing SKU: %s"
LOG_SKIP_KIT_DUE_TO_AMAZON_FAILURE = "Skipping kit SKU %s due to Amazon data fetch failure."
LOG_AMAZON_SNAPSHOT_STORED_KIT = "Amazon snapshot stored for kit item: %s"
LOG_ERROR_IN_STORE_AMAZON_SNAPSHOTS_SERVICE = "Error in store_the_amazon_snapshots_service"
LOG_SKIP_INVENTORY_DUE_TO_NETSUITE_ID_FAILURE = "Skipping inventory SKU %s due to netsuite internal id fetch failure."
LOG_NETSUITE_SNAPSHOT_STORED_INVENTORY = "Amazon snapshot stored for inventory item: %s"
LOG_NETSUITE_SNAPSHOT_STORED_KIT = "Netsuite snapshot stored for kit item: %s"
LOG_ERROR_IN_COMPARISON_SERVICE = "Error in comparison_service"
PRICE = "price"
STOCK = "stock"
FILE_UPLOAD_HISTORY = "File Upload History"
FILE_HISTORY_NOT_FOUND="File history not found"
PROFILE_RETRIEVED_SUCCESSFULLY = "Profile retrieved successfully"
FILE_NOT_FOUND = "File not found"
COMPARISON_DATA = "Comparison Data"
KIT_QUANTITY = "kit_quantity"
YOU_DONT_HAVE_ENOUGH_PERMISSIONS = "You dont have enough permissions to access this file"

INITIATED_STATUS_PENDING = "Initiated"
INGESTED_STATUS = "Ingested"

FILE_IS_NOT_PROCESSED = "File is not processed yet"
INVALID_COMPARISON_TYPE = "Invalid comparison type: {}"
INVALID_RESULT_FILTER = "Invalid result filter: {}"
INVALID_PLATFORM_FILTER = "Invalid platform filter: {}"


