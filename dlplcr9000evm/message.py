from __future__ import annotations
from dataclasses import dataclass, field, fields
from dlplcr9000evm.commands import Command, COMMAND_SIZE, COMMAND_ORDER


@dataclass
class Flag:
    destination: int = field(default=0, metadata={"bits": 3, "offset": 0})
    reserved: int = field(default=0, metadata={"bits": 2, "offset": 3})
    error: int = field(default=0, metadata={"bits": 1, "offset": 5})
    reply: int = field(default=0, metadata={"bits": 1, "offset": 6})
    read_or_write: int = field(default=0, metadata={"bits": 1, "offset": 7})

    @classmethod
    def from_int(cls, byte: int) -> Flag:
        values = []
        for current_field in fields(cls):
            mask = (1 << current_field.metadata["bits"]) - 1
            values.append((byte >> current_field.metadata["offset"]) & mask)
        return cls(*values)

    def to_int(self) -> int:
        byte = 0
        for current_field in fields(self):
            mask = (1 << current_field.metadata["bits"]) - 1
            byte |= (getattr(self, current_field.name) & mask) << current_field.metadata["offset"]
        return byte


@dataclass
class Header:
    flag: Flag = field(default_factory=Flag, metadata={"size": 1, "order": "little"})
    sequence: int = field(default=0, metadata={"size": 1, "order": "little"})
    length: int = field(default=0, metadata={"size": 2, "order": "little"})

    @classmethod
    def get_size(cls) -> int:
        return sum(field.metadata["size"] for field in fields(cls))

    @classmethod
    def from_bytes(cls, buffer: bytes) -> Header:
        offset = 0
        values = []
        for current_field in fields(cls):
            if not isinstance(getattr(cls(), current_field.name), Flag):
                values.append(
                    int.from_bytes(
                        buffer[offset : (offset + current_field.metadata["size"])],
                        current_field.metadata["order"],
                    )
                )
            else:
                values.append(
                    Flag.from_int(
                        int.from_bytes(
                            buffer[offset : (offset + current_field.metadata["size"])],
                            current_field.metadata["order"],
                        )
                    )
                )
            offset += current_field.metadata["size"]
        return cls(*values)

    def to_bytes(self) -> bytes:
        buffer = b""
        for current_field in fields(self):
            if not isinstance(getattr(self, current_field.name), Flag):
                buffer += getattr(self, current_field.name).to_bytes(
                    current_field.metadata["size"], current_field.metadata["order"]
                )
            else:
                buffer += (
                    getattr(self, current_field.name)
                    .to_int()
                    .to_bytes(current_field.metadata["size"], current_field.metadata["order"])
                )
        return buffer


@dataclass
class Request:
    header: Header = field(default_factory=Header)
    command: Command = field(default=None)
    data: list[int] = field(default_factory=list)

    @classmethod
    def from_bytes(cls, buffer: bytes) -> Request:
        offset = 0
        values = []
        for current_field in fields(cls):
            if isinstance(getattr(cls(), current_field.name), Header):
                values.append(Header.from_bytes(buffer[offset : (offset + Header.get_size())]))
                offset += Header.get_size()
            elif isinstance(getattr(cls(), current_field.name), Command):
                command_value = int.from_bytes(buffer[offset : (offset + COMMAND_SIZE)], COMMAND_ORDER)
                values.append(
                    next(
                        (member for _, member in Command.__members__.items() if member.usb == command_value),
                        None,
                    )
                )
                offset += COMMAND_SIZE
            else:
                values.append(list(buffer[offset:]))
        return cls(*values)

    def to_bytes(self) -> bytes:
        buffer = b""
        for current_field in fields(self):
            if isinstance(getattr(self, current_field.name), Header):
                buffer += getattr(self, current_field.name).to_bytes()
            elif isinstance(getattr(self, current_field.name), Command):
                buffer += getattr(self, current_field.name).usb.to_bytes(COMMAND_SIZE, COMMAND_ORDER)
            else:
                buffer += bytes(getattr(self, current_field.name))
        return buffer


@dataclass
class Response:
    header: Header = field(default_factory=Header)
    data: list[int] = field(default_factory=list)

    @classmethod
    def from_bytes(cls, buffer: bytes) -> Response:
        offset = 0
        values = []
        for current_field in fields(cls):
            if isinstance(getattr(cls(), current_field.name), Header):
                values.append(Header.from_bytes(buffer[offset : (offset + Header.get_size())]))
                offset += Header.get_size()
            else:
                values.append(list(buffer[offset:]))
        return cls(*values)

    def to_bytes(self) -> bytes:
        buffer = b""
        for current_field in fields(self):
            if isinstance(getattr(self, current_field.name), Header):
                buffer += getattr(self, current_field.name).to_bytes()
            else:
                buffer += bytes(getattr(self, current_field.name))
        return buffer


if __name__ == "__main__":
    pass
