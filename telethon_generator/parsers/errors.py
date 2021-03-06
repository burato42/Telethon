import csv

from ..utils import snake_to_camel_case

# Core base classes depending on the integer error code
KNOWN_BASE_CLASSES = {
    303: 'InvalidDCError',
    400: 'BadRequestError',
    401: 'UnauthorizedError',
    403: 'ForbiddenError',
    404: 'NotFoundError',
    406: 'AuthKeyError',
    420: 'FloodError',
    500: 'ServerError',
}

# Give better semantic names to some captures
# TODO Move this to the CSV?
CAPTURE_NAMES = {
    'FloodWaitError': 'seconds',
    'FloodTestPhoneWaitError': 'seconds',
    'TakeoutInitDelayError': 'seconds',
    'FileMigrateError': 'new_dc',
    'NetworkMigrateError': 'new_dc',
    'PhoneMigrateError': 'new_dc',
    'UserMigrateError': 'new_dc',
    'FilePartMissingError': 'which'
}


def _get_class_name(error_code):
    """
    Gets the corresponding class name for the given error code,
    this either being an integer (thus base error name) or str.
    """
    if isinstance(error_code, int):
        return KNOWN_BASE_CLASSES.get(
            error_code, 'RPCError' + str(error_code).replace('-', 'Neg')
        )

    return snake_to_camel_case(
        error_code.replace('FIRSTNAME', 'FIRST_NAME').lower(), suffix='Error')


class Error:
    def __init__(self, codes, name, description):
        # TODO Some errors have the same name but different integer codes
        # Should these be split into different files or doesn't really matter?
        # Telegram isn't exactly consistent with returned errors anyway.
        self.int_code = codes[0]
        self.str_code = name
        self.subclass = _get_class_name(codes[0])
        self.subclass_exists = codes[0] in KNOWN_BASE_CLASSES
        self.description = description

        self.has_captures = '_X' in name
        if self.has_captures:
            self.name = _get_class_name(name.replace('_X', ''))
            self.pattern = name.replace('_X', r'_(\d+)')
            self.capture_name = CAPTURE_NAMES.get(self.name, 'x')
        else:
            self.name = _get_class_name(name)
            self.pattern = name
            self.capture_name = None


def parse_errors(csv_file):
    """
    Parses the input CSV file with columns (name, error codes, description)
    and yields `Error` instances as a result.
    """
    with open(csv_file, newline='') as f:
        f = csv.reader(f)
        next(f, None)  # header
        for line, (name, codes, description) in enumerate(f, start=2):
            try:
                codes = [int(x) for x in codes.split()] or [400]
            except ValueError:
                raise ValueError('Not all codes are integers '
                                 '(line {})'.format(line)) from None

            yield Error([int(x) for x in codes], name, description)
