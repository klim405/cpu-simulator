import enum


class WriteSignal(enum.Enum):
    WRITE_AC = 1  # Write accumulator register
    WRITE_BR = 2  # Write buffer register
    WRITE_DR = 4  # Write data register
    WRITE_CR = 8  # Write command register
    WRITE_CPH = 16  # Write command pointer height byte
    WRITE_CPL = 32  # Write command register lower byte
    WRITE_SPH = 64  # Write stack pointer height byte
    WRITE_SPL = 128  # Write stack register lower byte
    WRITE_OR = 256  # Write output register
    WRITE_ARH = 512  # Write address register height byte
    WRITE_ARL = 1024  # Write address register lower byte


class WriteFlagSignal(enum.Enum):
    RESERVED = 1
    WRITE_W = 2
    WRITE_O = 8
    WRITE_C = 16
    WRITE_V = 32
    WRITE_Z = 64
    WRITE_N = 128


WRITE_NZVC_SIGNALS = [
    WriteFlagSignal.WRITE_N,
    WriteFlagSignal.WRITE_Z,
    WriteFlagSignal.WRITE_V,
    WriteFlagSignal.WRITE_C
]


class ALUSourceASignal(enum.Enum):
    ZERO = 0
    READ_AC = 1
    READ_BR = 2
    READ_PS = 3
    READ_IR = 4


class ALUSourceBSignal(enum.Enum):
    ZERO = 0
    ONE = 1
    READ_DR = 2
    READ_CR = 3
    READ_CPH = 4
    READ_CPL = 5
    READ_SPH = 6
    READ_SPL = 7


class ALUSignal(enum.Enum):
    ADD = 0
    SUB = 1
    AND = 2
    OR = 3
