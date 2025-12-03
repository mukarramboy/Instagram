import re
from apps.users.models import AuthType

email_regex = re.compile(
    r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"
)

phone_regex_uz = re.compile(
    r"^(?:\+998|998|0)(?:33|71|77|55|90|91|93|94|95|97|98|99|88|66|67|76|78)([0-9]{7})$"
)

username_regex = re.compile(r"^[a-zA-Z0-9_.-]+$")

def email_or_phone_validator(value: str):
    if email_regex.match(value):
        return AuthType.Email
    elif phone_regex_uz.match(value):
        return AuthType.Phone
    else:
        raise ValueError("Invalid email or phone number format.")
    

def check_user_type(user_input):
    # phone_number = phonenumbers.parse(user_input)
    if email_regex.match(user_input):
        user_input = 'email'
    elif phone_regex_uz.match(user_input):
        user_input = 'phone'
    elif username_regex.match(user_input):
        user_input = 'username'
    else:
        raise ValueError("Invalid user input format.")
    return user_input

