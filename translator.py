import re
from typing import List, Dict

MNEMONIC = {
    'NOP': 0x00,
    'HLT': 0x10,
    'CLA': 0x20,
    'CLC': 0x28,
    'CMC': 0x30,
    'NOT': 0x38,
    'INC': 0x48,
    'DEC': 0x40,
    'NEG': 0x4C,
    'POP': 0x58,
    'PUSH': 0x50
}


class AssemblerCommand:
    def __init__(self, operation: str | None = None, operand: str | None = None):
        self.operation = operation.upper()
        self.operand = operand

    def has_operand(self) -> bool:
        return self.operand is not None

    def get_encoded_length(self) -> int:
        if self.operand is None:
            return 1
        return 3

    def encode(self, operand_address: int | None = None) -> bytes:
        if operand_address is None and self.operand is not None:
            raise Exception('Operand must not be None')
        if self.operand is None:
            return MNEMONIC[self.operation].to_bytes(1, 'big')
        return ((MNEMONIC[self.operation] << 16) + operand_address).to_bytes(3, 'big')


class AssemblerData:
    def __init__(self, value: int | str):
        self.value = value

    def get_encoded_length(self) -> int:
        if isinstance(self.value, int):
            return 1
        return len(self.value) + 1

    def encode(self) -> bytes:
        if isinstance(self.value, int):
            return self.value.to_bytes(1, 'big')
        else:
            str_value = self.value.encode('ascii')
            str_length = len(str_value)
            bin_value = str_length.to_bytes(1, 'big') + str_value
            return bin_value


class AssemblerTranslator:
    def __init__(
            self,
            assembler_filename: str,
            mem_filename: str,
            text_section_addr: int = 0x0000,
            data_section_addr: int = 0x6000):
        self.labels: Dict[str, int] = {}
        self.commands: List[AssemblerCommand] = []
        self.data: List[AssemblerData] = []
        self.text_section_start = text_section_addr
        self.data_section_start = data_section_addr
        self.text_pointer = text_section_addr
        self.data_pointer = data_section_addr
        self.assembler_filename = assembler_filename
        self.mem_filename = mem_filename

    def add_label(self, label: str | None = None, is_data: bool = False) -> None:
        if label is None:
            return
        label = label.lower()
        if is_data:
            self.labels[label] = self.data_pointer
        else:
            self.labels[label] = self.text_pointer

    def translate_command(self, line: str) -> None:
        match = re.match(r'((\w+)\s*:)?\s*(\w+)(\s+(\w+))?', line.strip())
        if match is None:
            raise Exception(f'Syntax error in {line}')
        self.add_label(match.group(2))
        command = AssemblerCommand(operation=match.group(3), operand=match.group(5))
        self.commands.append(command)
        self.text_pointer += command.get_encoded_length()

    def translate_data(self, line: str) -> None:
        match = re.match(r'((\w+)\s*:)\s*([\'"]([\w\s]+)[\'"])|(\d+)', line.strip())
        if match is None:
            raise Exception(f'Syntax error in {line}')
        self.add_label(match.group(2))
        data = AssemblerData(match.group(4) or match.group(5))
        self.data.append(data)
        self.data_pointer += data.get_encoded_length()

    def read_assembler(self) -> None:
        with open(self.assembler_filename, 'r') as assembler:
            current_section_is_text = True
            for line in assembler.readlines():
                line = line.strip()
                if not line:
                    continue
                if line.startswith('.'):
                    current_section_is_text = (line.lower() == '.text')
                    continue
                if current_section_is_text:
                    self.translate_command(line)
                else:
                    self.translate_data(line)

    def write_text(self) -> None:
        with open(self.mem_filename, 'r+b') as mem:
            mem.seek(self.text_section_start)
            for command in self.commands:
                operand_addr = None
                if command.has_operand():
                    operand_addr = self.labels[command.operand]
                mem.write(command.encode(operand_addr))

    def write_data(self) -> None:
        with open(self.mem_filename, 'r+b') as mem:
            mem.seek(self.data_section_start)
            for data in self.data:
                mem.write(data.encode())

    def translate(self):
        self.read_assembler()
        self.write_text()
        self.write_data()
