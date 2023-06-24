from enum import Enum


class DLPLCR9000EVMException(Exception):
    pass


class DLPLCR9000EVMWriteDataError(Exception):
    pass


class DLPLCR9000EVMReadDataError(Exception):
    pass


class DLPLCR9000EVMReadDataResponseError(Exception):
    pass


class DLPC900Error(Exception):
    pass


class DLPC900ErrorCode(Enum):
    NO_ERROR = 0
    BATCH_FILE_CHECKSUM_ERROR = 1
    DEVICE_FAILURE = 2
    INVALID_COMMAND_NUMBER = 3
    INCOMPATIBLE_CONTROLLER_AND_DMD_COMBINATION = 4
    COMMAND_NOT_ALLOWED_IN_CURRENT_MODE = 5
    INVALID_COMMAND_PARAMETER = 6
    ITEM_REFERRED_BY_THE_PARAMETER_IS_NOT_PRESENT = 7
    OUT_OF_RESOURCE_RAM_OR_FLASH = 8
    INVALID_BMP_COMPRESSION_TYPE = 9
    PATTERN_BIT_NUMBER_OUT_OF_RANGE = 10
    PATTERN_BMP_NOT_PRESENT_IN_FLASH = 11
    PATTERN_DARK_TIME_IS_OUT_OF_RANGE = 12
    SIGNAL_DELAY_PARAMETER_IS_OUT_OF_RANGE = 13
    PATTERN_EXPOSURE_TIME_IS_OUT_OF_RANGE = 14
    PATTERN_NUMBER_IS_OUT_OF_RANGE = 15
    INVALID_PATTERN_DEFINITION = 16
    PATTERN_IMAGE_MEMORY_ADDRESS_IS_OUT_OF_RANGE = 17
    NOT_DEFINED = None
    INTERNAL_ERROR = 255


def error_handle(method):
    def wrapper(self, *args, **kwargs):
        try:
            result = method(self, *args, **kwargs)
        except DLPLCR9000EVMReadDataResponseError:
            if not method.__name__ in ["get_error_code", "get_error_description"]:
                error_code = self.get_error_code()
                error_description = self.get_error_description()
                raise DLPC900Error(f"{[error_code]}: {error_description}")
            else:
                return method(self, *args, **kwargs)
        else:
            if not method.__name__ in ["get_error_code", "get_error_description"]:
                error_code = self.get_error_code()
                if error_code is not DLPC900ErrorCode.NO_ERROR:
                    error_description = self.get_error_description()
                    raise DLPC900Error(f"{[error_code]}: {error_description}")

        return result

    return wrapper


if __name__ == "__main__":
    pass
