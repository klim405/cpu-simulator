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


class FlagSignal(enum.Enum):
    WRITE_B = 1
    WRITE_W = 2
    WRITE_O = 4
    WRITE_I = 8
    WRITE_C = 16
    WRITE_V = 32
    WRITE_Z = 64
    WRITE_N = 128


WRITE_NZVCB_SIGNALS = [
    FlagSignal.WRITE_N,
    FlagSignal.WRITE_Z,
    FlagSignal.WRITE_V,
    FlagSignal.WRITE_C,
    FlagSignal.WRITE_B
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


class ALUAddCSignal(enum.Enum):
    NULL = 0
    ADD_C = 1
    ADD_B = 2
    ADD_1 = 3
