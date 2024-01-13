import enum
from typing import List

from signals import WriteSignal, ALUSignal, ALUSourceASignal, ALUSourceBSignal, WriteFlagSignal


class SegmentMask(enum.Enum):
    TYPE_MASK = (0b1, 31)
    STORE_MASK = (0b1, 30)
    LOAD_MASK = (0b1, 29)
    WRITE_MASK = (0b11111111111, 18)
    CONDITION_VALUE_MASK = (0b1, 27)
    ADDR_MASK = (0b11111111, 18)
    WRITE_FLAG_MASK = (0b11111111, 10)
    CONDITION_MASK = (0b11111111, 10)
    ALU_NEG_A_MASK = (0b1, 9)
    ALU_MODE_MASK = (0b11, 7)
    ALU_ADD_C_MASK = (0b1, 6)
    READ_A_MASK = (0b111, 3)
    READ_B_MASK = (0b111, 0)


class MicroInstruction:
    def __init__(self, instruction):
        self.instruction = instruction

    def get_segment(self, mask: SegmentMask):
        offset = mask.value[1]
        bits_mask = mask.value[0]
        return (self.instruction & (bits_mask << offset)) >> offset

    def is_control(self) -> bool:
        return bool(self.get_segment(SegmentMask.TYPE_MASK))

    def get_store_signal(self) -> int:
        return self.get_segment(SegmentMask.STORE_MASK)

    def get_load_signal(self) -> int:
        return self.get_segment(SegmentMask.LOAD_MASK)

    def get_write_signal(self) -> List[WriteSignal]:
        if self.is_control():
            raise RuntimeError('Write signal segment can not be decoded in control micro-instruction')
        encoded_signals = self.get_segment(SegmentMask.WRITE_MASK)
        decoded_signals = []
        for sig in WriteSignal:
            if encoded_signals & sig.value:
                decoded_signals.append(sig)
        return decoded_signals

    def get_alu_neg_signal(self) -> int:
        return self.get_segment(SegmentMask.ALU_NEG_A_MASK)

    def get_alu_signal(self) -> ALUSignal:
        return ALUSignal(self.get_segment(SegmentMask.ALU_MODE_MASK))

    def get_alu_src_a_signal(self) -> ALUSourceASignal:
        return ALUSourceASignal(self.get_segment(SegmentMask.READ_A_MASK))

    def get_alu_src_b_signal(self) -> ALUSourceBSignal:
        return ALUSourceBSignal(self.get_segment(SegmentMask.READ_B_MASK))

    def get_alu_add_c_signal(self):
        return self.get_segment(SegmentMask.ALU_ADD_C_MASK)

    def get_address(self):
        return self.get_segment(SegmentMask.ADDR_MASK)

    def get_write_flag_signals(self) -> List[WriteFlagSignal]:
        encoded_signals = self.get_segment(SegmentMask.WRITE_FLAG_MASK)
        decoded_signals = []
        for sig in WriteFlagSignal:
            if encoded_signals & sig.value:
                decoded_signals.append(sig)
        return decoded_signals

    def get_condition_value(self):
        return self.get_segment(SegmentMask.CONDITION_VALUE_MASK)

    def get_condition_mask(self):
        return self.get_segment(SegmentMask.CONDITION_MASK)
