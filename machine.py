from typing import Literal

from microcode import MicroInstruction
from signals import ALUSourceASignal, ALUSourceBSignal, WriteSignal, ALUSignal, FlagSignal, WRITE_NZVCB_SIGNALS, \
    ALUAddCSignal
from utils.bits import replace_bits, join_bits, invert_bits

REG_MASK = 0b11111111


class ALU:
    src_a = 0
    src_b = 0
    out = 0
    nzvc = [0, 0, 0, 0]

    def set_src_a(self, val):
        self.src_a = val

    def set_src_b(self, val):
        self.src_b = val

    def not_a(self):
        self.src_a = (1 << 8) - 1 - self.src_a

    def not_b(self):
        self.src_b = (1 << 8) - 1 - self.src_b

    def calc_output(self, signal: ALUSignal, c_flag_value: int = 0):
        match signal:
            case ALUSignal.ADD:
                self._add(c_flag_value)
            case ALUSignal.SUB:
                if c_flag_value:
                    raise RuntimeError('Warning: C flag value is not supported by sub operation')
                self._sub()
            case ALUSignal.AND:
                self._and()
            case ALUSignal.OR:
                self._or()
        self._set_nzvc()

    def _add(self, c_flag_value: int = 0):
        if c_flag_value not in [0, 1]:
            raise RuntimeError(f'Warning: C flag value is not be able to equal {c_flag_value}')
        self.out = self.src_a + self.src_b + c_flag_value

    def _sub(self):
        self.not_b()
        self._add(1)

    def _and(self):
        self.out = self.src_a & self.src_b

    def _or(self):
        self.out = self.src_a | self.src_b

    def _set_n(self):
        self.nzvc[3] = (self.out >> 7) & 1

    def _set_z(self):
        self.nzvc[2] = int(self.out & 255 == 0)

    def _set_v(self):
        a7 = (self.src_a >> 7) & 1
        b7 = (self.src_b >> 7) & 1
        not_y7 = (invert_bits(self.out) >> 7) & 1
        self.nzvc[1] = (a7 & b7) | (a7 & not_y7) | (b7 & not_y7)

    def _set_c(self):
        self.nzvc[0] = int(self.out & 256 != 0)

    def _set_nzvc(self):
        self._set_n()
        self._set_z()
        self._set_v()
        self._set_c()

    def get_out(self) -> int:
        return self.out & REG_MASK

    def get_nzvc(self) -> int:
        return join_bits(self.nzvc)


class DataPath:
    # SrcA
    ac = 0  # 001
    br = 0  # 010
    sr = 2  # 011
    ir = 0  # 100 Read only

    # SrcB
    dr = 0  # 001
    cr = 0  # 010
    cp = 0  # 011
    sp = 0xff  # 100

    # Write only
    _or = 0
    ar = 0

    def __init__(self, memory_filename: str = 'mem.bin'):
        self.memory_filename = memory_filename
        self.ALU = ALU()

    def read_src_a(self, read_signal: ALUSourceASignal):
        """ (AC | BR | SR | IR ) ->  Src A """
        val = 0
        match read_signal:
            case ALUSourceASignal.READ_AC:
                val = self.ac
            case ALUSourceASignal.READ_BR:
                val = self.br
            case ALUSourceASignal.READ_IR:
                val = self.ir
            case ALUSourceASignal.READ_PS:
                val = self.sr
        self.ALU.set_src_a(val)

    def read_src_b(self, read_signal: ALUSourceBSignal):
        """  ->  Src B """
        val = 0
        match read_signal:
            case ALUSourceBSignal.ONE:
                val = 1
            case ALUSourceBSignal.READ_DR:
                val = self.dr
            case ALUSourceBSignal.READ_CR:
                val = self.cr
            case ALUSourceBSignal.READ_CP:
                val = self.cp
            case ALUSourceBSignal.READ_SP:
                val = self.sp
        self.ALU.set_src_b(val)

    def write_register(self, write_signal: WriteSignal):
        """ ALU output -> target reg """
        match write_signal:
            case WriteSignal.WRITE_AC:
                self.ac = self.ALU.get_out()
            case WriteSignal.WRITE_BR:
                self.br = self.ALU.get_out()
            case WriteSignal.WRITE_DR:
                self.dr = self.ALU.get_out()
            case WriteSignal.WRITE_CR:
                self.cr = self.ALU.get_out()
            case WriteSignal.WRITE_CP:
                self.cp = self.ALU.get_out()
            case WriteSignal.WRITE_SP:
                self.sp = self.ALU.get_out()
            case WriteSignal.WRITE_OR:
                self._or = self.ALU.get_out()
            case WriteSignal.WRITE_AR:
                self.ar = self.ALU.get_out()

    def write_flag(self, signal: FlagSignal, use_alu_out=False) -> None:
        if use_alu_out:
            reg_in = self.ALU.get_out()
        else:
            reg_in = (self.ALU.get_nzvc() << 4) + (self.ALU.get_nzvc() & 1) + (self.sr & 0b1110)
        if signal in WRITE_NZVCB_SIGNALS:
            self.sr = replace_bits(self.sr, reg_in, signal.value)
        else:
            self.sr = replace_bits(self.sr, self.ALU.get_out(), signal.value)

    def load_mem(self):
        """ MEM(AR) -> DR """
        with open(self.memory_filename, 'rb') as mem:
            mem.seek(self.ar)
            self.dr = int.from_bytes(mem.read(1), 'big', signed=False)

    def store_mem(self):
        """ DR -> MEM(AR) """
        with open(self.memory_filename, 'r+b') as mem:
            mem.seek(self.ar)
            mem.write(self.dr.to_bytes(1, 'big', signed=False))

    def run_alu(self, alu_signal: ALUSignal, not_a_signal: int | bool, add_c_signal: ALUAddCSignal):
        if not_a_signal:
            self.ALU.not_a()
        if add_c_signal == ALUAddCSignal.ADD_C:
            c = (self.sr >> 4) & 1
            self.ALU.calc_output(alu_signal, c)
        elif add_c_signal == ALUAddCSignal.ADD_B:
            buff_c = self.sr & 1
            self.ALU.calc_output(alu_signal, buff_c)
        elif add_c_signal == ALUAddCSignal.ADD_1:
            self.ALU.calc_output(alu_signal, 1)
        else:
            self.ALU.calc_output(alu_signal)

    def get_w_flag(self) -> int:
        return (self.sr >> 1) & 1

    def __str__(self):
        s = []
        for i in ['ac', 'br', 'sr', 'ir', '_or', 'dr', 'cr', 'cp', 'sp']:
            s.append(hex(getattr(self, i))[2:].zfill(2))
        return ' | '.join(s).upper()


class CPU:
    tick = 0
    mc = 0  # microcode pointer

    def __init__(
            self,
            memory_filename: str = 'files/mem.bin',
            microcode_filename: str = 'files/microcode.bin',
            log_mode: Literal['instr', 'tick'] = 'tick'):
        self.microcode_filename = microcode_filename
        self.data_path = DataPath(memory_filename)
        self.log_mode = log_mode

    def get_instruction(self) -> MicroInstruction:
        with open(self.microcode_filename, 'rb') as microcode:
            microcode.seek(self.mc * 5)
            return MicroInstruction(microcode.read(5))

    def activate_alu(self, instr):
        self.data_path.read_src_a(instr.get_alu_src_a_signal())
        self.data_path.read_src_b(instr.get_alu_src_b_signal())
        self.data_path.run_alu(
            instr.get_alu_signal(),
            instr.get_alu_neg_signal(),
            instr.get_alu_add_c_signal()
        )

    def change_address(self, addr):
        self.mc = addr

    def set_next_address(self):
        self.mc += 1

    def execute_control_instruction(self, instr: MicroInstruction):
        self.activate_alu(instr)
        selected_bit = bool(self.data_path.ALU.get_out() & instr.get_condition_mask())
        target_bit = bool(instr.get_condition_value())
        if selected_bit == target_bit:
            self.change_address(instr.get_address())
        else:
            self.set_next_address()

    def execute_action_instruction(self, instr: MicroInstruction):
        if instr.get_store_signal():
            self.data_path.store_mem()
        if instr.get_load_signal():
            self.data_path.load_mem()
        self.activate_alu(instr)
        for sig in instr.get_write_signal():
            self.data_path.write_register(sig)
        for sig in instr.get_write_flag_signals():
            self.data_path.write_flag(sig, use_alu_out=instr.use_alu_out_for_sr())
        self.set_next_address()

    def execute_instruction(self):
        instr = self.get_instruction()
        if instr.is_control():
            self.execute_control_instruction(instr)
        else:
            self.execute_action_instruction(instr)

    def start(self, tick_limit=1000):
        print('ac | br | sr | ir | or | dr | cr | cp | sp')
        self.log()
        while self.tick <= tick_limit and self.data_path.get_w_flag():
            # print(self.get_instruction(), self.mc)
            self.execute_instruction()
            self.tick += 1
            self.log()

    def log(self):
        if self.log_mode == 'tick':
            print(self.tick, self.mc, self.data_path)
        else:
            if self.mc == 0:
                print(self.data_path)