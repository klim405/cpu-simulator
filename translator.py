import re
from enum import Enum
from functools import lru_cache
from typing import Dict, Literal, Tuple

from utils.bits import int_to_signed

MNEMONIC = {
    'NOP': 0x00,
    'HLT': 0x10,
    'CLA': 0x20,
    'CLC': 0x28,
    'CMC': 0x30,
    'NOT': 0x38,
    'INC': 0x4C,
    'DEC': 0x48,
    'NEG': 0x40,
    'POP': 0x50,
    'PUSH': 0x58,
    'IN': 0x68,
    'OUT': 0x60,
    'RET': 0x70,
    'AND': 0x80,
    'OR': 0x88,
    'ADD': 0x90,
    'ADC': 0x94,
    'CMP': 0x98,
    'SUB': 0x9C,
    'LD': 0xA0,
    'ST': 0xA8,
    'CALL': 0xB0,
    'JUMP': 0xB8,
    'JEQ': 0xC0,
    'JNE': 0xC4,
    'JPL': 0xC8,
    'JMI': 0xCC,
    'JCU': 0xD0,
    'JCS': 0xD4,
    'JVU': 0xD8,
    'JVS': 0xDC,
    'JGT': 0xE0,
    'JGE': 0xE4,
    'JLT': 0xE8,
    'JLE': 0xEC,
}


def get_opcode(asm_command: str) -> int:
    return MNEMONIC[asm_command.upper()]


class AddressMode(Enum):
    ABSOLUTE = 0b00
    RELATIVE = 0b01
    BASE = 0b10
    STACK = 0b11


ASM_LINE_PATTERN = (r'(([a-zA-Z_]\w*)\s*:)?\s*'
                    r'((([a-zA-Z_]\w*)(\s+(((~)?([a-zA-Z_]\w*))|(([$~+-@])(\d+))))?)|(["\'](.*)["\'])|([-]?\d+))')
RE_ASM_LINE_TEMPLATE = re.compile(ASM_LINE_PATTERN)


@lru_cache
def parse_asm_line(line: str):
    return RE_ASM_LINE_TEMPLATE.match(line)


class ASMMatch:
    def __init__(self, line):
        self.match = parse_asm_line(line)

    def has_label(self) -> bool:
        return self.match.group(1) is not None

    def get_label(self) -> str:
        return self.match.group(2)

    def is_command(self) -> bool:
        return self.match.group(5) is not None

    def has_command_arg(self) -> bool:
        return self.match.group(7) is not None

    def arg_is_label(self) -> bool:
        return self.match.group(10) is not None

    def get_arg_as_label(self) -> str:
        return self.match.group(10)

    def get_arg_as_int(self) -> int:
        return int(self.match.group(13))

    def get_addr_mode(self):
        addr = self.match.group(12) if self.match.group(12) else '+'
        match addr:
            case '@':
                return AddressMode.ABSOLUTE
            case '+':
                return AddressMode.BASE
            case '-':
                return AddressMode.BASE
            case '~':
                return AddressMode.RELATIVE
            case '$':
                return AddressMode.STACK

    def get_opcode(self) -> int:
        return get_opcode(self.match.group(5))

    def is_string(self) -> bool:
        return self.match.group(15) is not None

    def to_string(self) -> str:
        return self.match.group(15)

    def is_digit(self) -> bool:
        return self.match.group(16) is not None

    def to_int(self) -> int:
        return int(self.match.group(16))

    def get_size(self) -> int:
        if self.is_string():
            return len(self.to_string()) + 1
        elif self.has_command_arg():
            return 2
        else:
            return 1


class TranslatorASM:
    def __init__(self, asm_filename: str, mem_filename: str, text_offset: int = 0, data_offset: int = 150) -> None:
        self.data_offset = data_offset
        self.text_offset = text_offset
        self.current_addr: int = 0
        self.asm_filename = asm_filename
        self.mem_filename = mem_filename
        self.text_ptr_sum: int = 0
        self.data_ptr_sum: int = 0
        self.labels: Dict[str, Tuple[int, Literal['text', 'data']]] = {}

    def translate(self):
        self.init_labels()
        self.write_memory()

    def init_labels(self):
        with open(self.asm_filename, 'r') as asm:
            current_section = 'text'
            for line in asm.readlines():
                line = line.strip()
                if line.startswith('.'):
                    current_section = 'data' if line[1:] == 'data' else 'text'
                    continue
                if line:
                    print("???", line)
                    self.try_extract_label(line, current_section)

    def try_extract_label(self, line: str, section: Literal['text', 'data']) -> None:
        match = ASMMatch(line)
        if section == 'text':
            if match.has_label():
                self.labels[match.get_label()] = (self.text_ptr_sum, 'text')
            self.text_ptr_sum += match.get_size()
        else:
            if match.has_label():
                self.labels[match.get_label()] = (self.data_ptr_sum, 'data')
            self.data_ptr_sum += match.get_size()

    def write_memory(self) -> None:
        with (open(self.asm_filename, 'r') as asm, open(self.mem_filename, 'r+b') as mem):
            for line in asm.readlines():
                line = line.strip()
                if line == '.text':
                    mem.seek(self.text_offset)
                    self.current_addr = self.text_offset
                    continue
                elif line == '.data':
                    mem.seek(self.data_offset)
                    self.current_addr = self.data_offset
                    continue
                if line:
                    print('<<<', line)
                    match = ASMMatch(line)
                    print(match.match.groups())
                    mem.write(self.encode_line(match))
                    self.current_addr += match.get_size()

    def encode_line(self, match: ASMMatch) -> bytes:
        if match.is_digit():
            return int_to_signed(match.to_int()).to_bytes(1, 'big')
        elif match.is_string():
            val = match.to_string()
            return len(val).to_bytes(1, 'big') + val.encode('ascii')
        elif match.is_command():
            return self.encode_command(match)

    def encode_command(self, match: ASMMatch) -> bytes:
        cmd = match.get_opcode()
        if match.has_command_arg():
            cmd |= match.get_addr_mode().value
            cmd <<= 8
            if match.arg_is_label():
                cmd += self.calc_label_addr(match) & 255
            else:
                cmd += self.calc_int_addr(match) & 255
            return cmd.to_bytes(2, 'big')
        return cmd.to_bytes(1, 'big')

    def calc_label_addr(self, match: ASMMatch) -> int:
        label = match.get_arg_as_label()
        label_sum, label_section = self.labels[label]
        base_offset = label_sum - self.current_addr
        if label_section == 'text':
            base_offset += self.text_offset
        else:
            base_offset += self.data_offset
        return base_offset

    def calc_int_addr(self, match: ASMMatch) -> int:
        if match.get_addr_mode() == AddressMode.BASE:
            return int_to_signed(match.get_arg_as_int())
        return match.get_arg_as_int()
