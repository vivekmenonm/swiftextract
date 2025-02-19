import re

def is_valid_email(email):
    regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(regex, email) is not None

# Strong Password Validation Function
def is_strong_password(password):
    return (
        len(password) >= 8 and
        re.search(r'[A-Z]', password) and  # At least one uppercase letter
        re.search(r'[0-9]', password) and  # At least one number
        re.search(r'[\W_]', password)      # At least one special character
    )

# Username Validation Function
def is_valid_username(username):
    regex = r'^[a-zA-Z0-9_.-]{3,20}$'  # Allows letters, numbers, _ . - (3 to 20 chars)
    return re.match(regex, username) is not None