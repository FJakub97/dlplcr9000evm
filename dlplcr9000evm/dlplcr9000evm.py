import hid
from dlplcr9000evm.commands import COMMAND_SIZE, Command
from dlplcr9000evm.errors import (
    DLPLCR9000EVMException,
    DLPLCR9000EVMWriteDataError,
    DLPLCR9000EVMReadDataError,
    DLPLCR9000EVMReadDataResponseError,
    DLPC900ErrorCode,
    error_handle,
)
from dlplcr9000evm.message import Flag, Header, Request, Response
from enum import Enum


class DLPC900Controller(Enum):
    PRIMARY = "MASTER"
    SECONDARY = "SLAVE"


class DLPLCR9000EVM:
    MAXIMUM_READ_MESSAGE_DATA_LENGTH = 58
    MAXIMUM_WRITE_MESSAGE_DATA_LENGTH = 506
    USB_MAXIMUM_PACKET_SIZE = 64
    USB_MAXIMUM_READ_TIMEOUT_IN_MILLISECONDS = 10000

    def __init__(self, vendor_id: int = 0x0451, product_id: int = 0xC900) -> None:
        self.vendor_id = vendor_id
        self.product_id = product_id
        self.device = None
        self.__sequence_number = 0

    def connect(self) -> None:
        self.device = hid.device()
        self.device.open(self.vendor_id, self.product_id)

    def disconnect(self) -> None:
        self.device.close()

    def prepare_read_message(self, command: Command, data: list[int] | None = None) -> Request:
        if data is None:
            data = []

        if len(data) > self.MAXIMUM_READ_MESSAGE_DATA_LENGTH:
            raise DLPLCR9000EVMException(
                f"maximum allowed number of data bytes, in read message, is {self.MAXIMUM_READ_MESSAGE_DATA_LENGTH}"
            )

        request = Request(Header(Flag(0, 0, 0, 1, 1), self.__sequence_number, COMMAND_SIZE + len(data)), command, data)
        self.__sequence_number = (self.__sequence_number + 1) & 0xFF

        return request

    def prepare_write_message(self, command: Command, data: list[int] | None = None, reply: bool = False) -> Request:
        if data is None:
            data = []
        
        if len(data) > self.MAXIMUM_WRITE_MESSAGE_DATA_LENGTH:
            raise DLPLCR9000EVMException(
                f"maximum allowed number of data bytes, in write message, is {self.MAXIMUM_WRITE_MESSAGE_DATA_LENGTH}"
            )

        request = Request(
            Header(Flag(0, 0, 0, reply, 0), self.__sequence_number, COMMAND_SIZE + len(data)), command, data
        )
        self.__sequence_number = (self.__sequence_number + 1) & 0xFF

        return request

    def read_operation(self, request: Request) -> Response:
        if not request.header.flag.reply:
            raise DLPLCR9000EVMException("read operation cannot be performed because the reply bit is set to 0")

        request_as_bytes = request.to_bytes()
        request_as_bytes += bytes(self.USB_MAXIMUM_PACKET_SIZE - len(request_as_bytes))
        number_of_bytes_written = self.device.write(b"\x00" + request_as_bytes)

        if number_of_bytes_written != self.USB_MAXIMUM_PACKET_SIZE + 1:
            raise DLPLCR9000EVMWriteDataError("an error occured while writing data to the DLPLCR9000EVM device")

        number_of_bytes_to_read = max(Header.get_size() + request.command.payload_length, self.USB_MAXIMUM_PACKET_SIZE)
        read_buffer = self.device.read(number_of_bytes_to_read, self.USB_MAXIMUM_READ_TIMEOUT_IN_MILLISECONDS)

        if len(read_buffer) != self.USB_MAXIMUM_PACKET_SIZE:
            raise DLPLCR9000EVMReadDataError("an error occured while reading data from the DLPLCR9000EVM device")

        response = Response.from_bytes(read_buffer)

        if response.header.flag.error or not response.header.length:
            raise DLPLCR9000EVMReadDataResponseError("an error in the response received from the DLPLCR9000EVM device")

        return response

    def __write_operation(self, data: bytes, acknowledge: bool) -> int | Response:
        number_of_bytes_written = self.device.write(data)

        if number_of_bytes_written != self.USB_MAXIMUM_PACKET_SIZE + 1:
            raise DLPLCR9000EVMWriteDataError("an error occured while writing data to the DLPLCR9000EVM device")

        if acknowledge:
            read_buffer = self.device.read(self.USB_MAXIMUM_PACKET_SIZE, self.USB_MAXIMUM_READ_TIMEOUT_IN_MILLISECONDS)

            if len(read_buffer) != self.USB_MAXIMUM_PACKET_SIZE:
                raise DLPLCR9000EVMReadDataError("an error occured while reading data from the DLPLCR9000EVM device")

            response = Response.from_bytes(read_buffer)

            if response.header.flag.error:
                raise DLPLCR9000EVMReadDataResponseError(
                    "an error in the response received from the DLPLCR9000EVM device"
                )

            return response

        return number_of_bytes_written

    def write_operation(self, request: Request) -> list[int] | list[Response]:
        output = []

        if request.command in [Command.PATTERN_BMP_LOAD_PRIMARY, Command.PATTERN_BMP_LOAD_SECONDARY]:
            request.header.flag.reply = False

        acknowledge = request.header.flag.reply
        request_as_bytes = request.to_bytes()
        number_of_packets = (len(request_as_bytes) + self.USB_MAXIMUM_PACKET_SIZE - 1) // self.USB_MAXIMUM_PACKET_SIZE
        request_as_bytes += bytes((number_of_packets * self.USB_MAXIMUM_PACKET_SIZE) - len(request_as_bytes))

        for packet_number in range(number_of_packets):
            output.append(
                self.__write_operation(
                    b"\x00"
                    + request_as_bytes[
                        (packet_number * self.USB_MAXIMUM_PACKET_SIZE) : (
                            (packet_number + 1) * self.USB_MAXIMUM_PACKET_SIZE
                        )
                    ],
                    acknowledge,
                )
            )

        return output

    def get_error_code(self) -> DLPC900ErrorCode:
        request = self.prepare_read_message(Command.ERROR_CODE)
        response = self.read_operation(request)
        error_code = next(
            (member for _, member in DLPC900ErrorCode.__members__.items() if member.value == response.data[0]),
            DLPC900ErrorCode.NOT_DEFINED,
        )

        return error_code

    def get_error_description(self) -> str:
        request = self.prepare_read_message(Command.ERROR_DESCRIPTION)
        response = self.read_operation(request)
        error_description = "".join([chr(ascii_decimal_code) for ascii_decimal_code in response.data])

        return error_description

    @error_handle
    def get_pattern_display_mode(self) -> int:
        request = self.prepare_read_message(Command.DISPLAY_MODE_SELECTION)
        response = self.read_operation(request)

        return response.data[0]

    @error_handle
    def set_pattern_display_mode(self, pattern_display_mode: int) -> list[int] | list[Response]:
        request = self.prepare_write_message(Command.DISPLAY_MODE_SELECTION, [pattern_display_mode], True)
        response = self.write_operation(request)

        return response

    @error_handle
    def set_pattern_display_control(self, pattern_display_action: int) -> list[int] | list[Response]:
        request = self.prepare_write_message(Command.PATTERN_START_OR_STOP, [pattern_display_action], True)
        response = self.write_operation(request)

        return response

    @error_handle
    def get_pattern_display_invert_data(self):
        request = self.prepare_read_message(Command.PATTERN_DISPLAY_INVERT_DATA)
        response = self.read_operation(request)

        return response.data[0]

    @error_handle
    def set_pattern_display_invert_data(self, pattern_display_invert_data: bool):
        request = self.prepare_write_message(Command.PATTERN_DISPLAY_INVERT_DATA, [pattern_display_invert_data], True)
        response = self.write_operation(request)

        return response

    @error_handle
    def set_pattern_display_lut_configuration(self, number_of_lut_entries: int, number_of_patterns_in_sequence: int):
        request = self.prepare_write_message(
            Command.PATTERN_DISPLAY_LUT_CONFIGURATION,
            [
                number_of_lut_entries & 0xFF,
                (number_of_lut_entries >> 8) & 0xFF,
                number_of_patterns_in_sequence & 0xFF,
                (number_of_patterns_in_sequence >> 8) & 0xFF,
                (number_of_patterns_in_sequence >> 16) & 0xFF,
                (number_of_patterns_in_sequence >> 24) & 0xFF,
            ],
            True,
        )
        response = self.write_operation(request)

        return response

    @error_handle
    def set_pattern_display_lut_definition(
        self,
        pattern_index: int,
        pattern_exposure_in_microseconds: int,
        clear_pattern_after_exposure: bool,
        bit_depth: int,
        pattern_display_color: int,
        wait_for_trigger: bool,
        dark_display_time_in_microseconds: int,
        disable_trigger_2_output: bool,
        extended_bit_depth: bool,
        image_pattern_index: int,
        bit_position: int,
    ):
        byte_no_5 = (
            clear_pattern_after_exposure
            | (((bit_depth - 1) & 0x07) << 1)
            | ((pattern_display_color & 0x07) << 4)
            | (wait_for_trigger << 7)
        )
        byte_no_9 = disable_trigger_2_output | (extended_bit_depth << 1)
        byte_no_10_and_11 = (image_pattern_index & 0x7FF) | ((bit_position & 0x1F) << 11)
        request = self.prepare_write_message(
            Command.PATTERN_DISPLAY_LUT_DEFINITION,
            [
                pattern_index & 0xFF,
                (pattern_index >> 8) & 0xFF,
                pattern_exposure_in_microseconds & 0xFF,
                (pattern_exposure_in_microseconds >> 8) & 0xFF,
                (pattern_exposure_in_microseconds >> 16) & 0xFF,
                byte_no_5,
                dark_display_time_in_microseconds & 0xFF,
                (dark_display_time_in_microseconds >> 8) & 0xFF,
                (dark_display_time_in_microseconds >> 16) & 0xFF,
                byte_no_9,
                byte_no_10_and_11 & 0xFF,
                (byte_no_10_and_11 >> 8) & 0xFF,
            ],
            True,
        )
        response = self.write_operation(request)

        return response

    @error_handle
    def initialize_pattern_bmp_load(
        self, dlpc900_controller: DLPC900Controller, image_index: int, image_data_size: int
    ) -> list[int] | list[Response]:
        if dlpc900_controller is DLPC900Controller.PRIMARY:
            command = Command.INITIALIZE_PATTERN_BMP_LOAD_PRIMARY
        elif dlpc900_controller is DLPC900Controller.SECONDARY:
            command = Command.INITIALIZE_PATTERN_BMP_LOAD_SECONDARY
        else:
            raise DLPLCR9000EVMException("unsupported controller choice")

        request = self.prepare_write_message(
            command,
            [
                image_index & 0xFF,
                (image_index >> 8) & 0xFF,
                image_data_size & 0xFF,
                (image_data_size >> 8) & 0xFF,
                (image_data_size >> 16) & 0xFF,
                (image_data_size >> 24) & 0xFF,
            ],
            True,
        )
        response = self.write_operation(request)

        return response

    @error_handle
    def pattern_bmp_load(self, dlpc900_controller: DLPC900Controller, image_data: list[int]) -> int:
        number_of_bytes_written = 0

        if dlpc900_controller is DLPC900Controller.PRIMARY:
            command = Command.PATTERN_BMP_LOAD_PRIMARY
        elif dlpc900_controller is DLPC900Controller.SECONDARY:
            command = Command.PATTERN_BMP_LOAD_SECONDARY
        else:
            raise DLPLCR9000EVMException("unsupported controller choice")

        maximum_message_image_data_length = self.MAXIMUM_WRITE_MESSAGE_DATA_LENGTH - 2
        number_of_messages = (len(image_data) + (maximum_message_image_data_length - 1)) // (
            maximum_message_image_data_length
        )

        for message_number in range(number_of_messages):
            message_data = image_data[
                (message_number * maximum_message_image_data_length) : (
                    (message_number + 1) * maximum_message_image_data_length
                )
            ]
            message_size = len(message_data)
            request = self.prepare_write_message(
                command, [message_size & 0xFF, (message_size >> 8) & 0xFF] + message_data
            )
            response = self.write_operation(request)
            number_of_bytes_written += sum(response)

        return number_of_bytes_written


if __name__ == "__main__":
    pass
