from email_validator import EmailNotValidError, validate_email
from phonenumbers import NumberParseException, is_valid_number, parse


def is_phone_number(number: str):
    try:
        return is_valid_number(parse(number))

    except NumberParseException:
        return False


def normalize_email(email: str):
    try:

        # Check that the email address is valid. Turn on check_deliverability
        # for first-time validations like on account creation pages (but not
        # login pages).
        emailinfo = validate_email(email, check_deliverability=False)

        # After this point, use only the normalized form of the email address,
        # especially before going to a database query.
        return emailinfo.normalized

    except EmailNotValidError as e:

        # The exception message is human-readable explanation of why it's
        # not a valid (or deliverable) email address.
        return None
