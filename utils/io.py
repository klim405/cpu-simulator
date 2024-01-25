import os


def convert_to_ascii(symbol: str) -> int:
    return int.from_bytes(symbol.encode('ascii'), 'big', signed=False)


def convert_from_ascii(symbol: int) -> str:
    return str(int.to_bytes(symbol, 1, signed=False), encoding='ascii')


class InputFile:
    def __init__(self, input_filename: str) -> None:
        self.input_filename = input_filename
        self.pointer = 0
        self.size = os.path.getsize(self.input_filename)

    def has_next(self) -> bool:
        return self.pointer < self.size

    def get_symbol(self) -> int:
        with open(self.input_filename, 'r') as inp:
            inp.seek(self.pointer)
            self.pointer += 1
            return convert_to_ascii(inp.read(1))
