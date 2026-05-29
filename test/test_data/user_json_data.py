import uuid
from copy import deepcopy

user_data_payload = {
    "first_name": "Disha",
    "last_name": "Patel",
    "email": "dishaa@gmail.com",
    "password": "Disha@123456"
}

user_data_api_payload = {
    "first_name": "Manav",
    "last_name": "Patel",
    "email": "manav@gmail.com",
    "password": "Manav@123456",
}

# Invalid payloads
invalid_mail_user_payload = deepcopy(user_data_payload)
invalid_mail_user_payload["email"] = "invalid-email"

invalid_password_user_payload = deepcopy(user_data_payload)
invalid_password_user_payload["password"] = "short"

# Login payloads
user_login_payload = {
    "email": "manav@gmail.com",
    "password": "Manav@123456",
}

invalid_password_payload = {
    "email": "dishaa@gmail.com",
    "password": "WrongPassword123",
}

invalid_email_payload = {
    "email": "nonexistent.user@example.com",
    "password": "Disha@123456",
}

# Update profile payloads
update_user_payload = {
    "first_name": "Disha",
    "last_name": "Updated",
}

invalid_update_user_payload = {
    "first_name": "Di",
    "last_name": "@#",
}

# Forgot and reset password payloads
forget_password_payload = {
    "email": "manav@gmail.com",
}

reset_password_payload = {
    "current_password": "Admin@test123",
    "new_password": "Admin@test1234",
    "confirm_password": "Admin@test1234",
}

invalid_reset_password_payload = {
    "current_password": "WrongPassword123",
    "new_password": "Disha@654321",
    "confirm_password": "Disha@654321",
}

invalid_confirm_password = {
    "current_password": "Admin@test123",
    "new_password": "Manav@654321",
    "confirm_password": "MismatchPassword",
}