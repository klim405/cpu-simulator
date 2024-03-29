from typing import Literal

from microcode import MicroInstruction
from signals import ALUSourceASignal, ALUSourceBSignal, WriteSignal, ALUSignal, FlagSignal, WRITE_NZVCB_SIGNALS, \
    ALUAddCSignal
from utils.bits import replace_bits, join_bits
from utils.io import convert_from_ascii, InputFile

REG_MASK = 0b11111111


class ALU:
    src_a = 0
    src_b = 0
    out = 0
    nzvc = [0, 0, 0, 0]
    src_c_flag = 0

    def set_src_a(self, val):
        self.src_a = val

    def set_src_b(self, val):
        self.src_b = val

    def not_a(self):
        self.src_a = (1 << 8) - 1 - self.src_a

    def not_b(self):
        self.src_b = (1 << 8) - 1 - self.src_b

    def calc_output(self, signal: ALUSignal, c_flag_value: int = 0):
        self.src_c_flag = c_flag_value
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
        a = self.src_a & (128 - 1)
        b = self.src_b & (128 - 1)
        c7 = (a + b + self.src_c_flag) >> 7
        c8 = self.out >> 8
        self.nzvc[1] = c7 ^ c8

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

    def is_i_flag_set(self) -> bool:
        return bool((self.sr >> 3) & 1)

    def is_o_flag_set(self) -> bool:
        return bool((self.sr >> 2) & 1)

    def write_input(self, val: int):
        self.sr = replace_bits(self.sr, 255, 0b1000)
        self.ir = val

    def reed_output(self) -> int:
        self.sr = replace_bits(self.sr, 0, 0b0100)
        return self._or

    def __str__(self):
        s = []
        for i in ['ac', 'br', 'sr', 'ir', '_or', 'ar', 'dr', 'cr', 'cp', 'sp']:
            s.append(hex(getattr(self, i))[2:].zfill(2))
        return ' | '.join(s).upper()


class Logger:
    def __init__(self, log_filename: str = 'files/temp/log.txt',
                 log_mode: Literal['instr', 'tick'] = 'tick'):
        self.log_filename = log_filename
        self.log_mode = log_mode
        self.data_path: DataPath | None = None
        self.cpu: CPU | None = None
        self.log_counter = 0

    def bound(self, data_path: DataPath, cpu: 'CPU'):
        self.data_path = data_path
        self.cpu = cpu

    def write_in_log(self, line):
        with open(self.log_filename, 'a') as log_file:
            log_file.write(f'{line}\n')

    def log(self) -> None:
        if self.cpu is None or self.data_path is None:
            raise Exception('CPU or DataPath is None')
        self.log_label()
        if self.log_mode == 'instr' and self.cpu.mc == 0:
            self.write_in_log(self.get_reg_vals())
            self.log_counter += 1
        elif self.log_mode == 'tick':
            self.write_in_log(self.get_reg_and_tick_vals())
            self.log_counter += 1

    def log_label(self) -> None:
        if self.log_counter % 20 == 0:
            if self.log_mode == 'tick':
                self.write_in_log(self.get_reg_labels_with_tick())
            elif self.cpu.mc == 0:
                self.write_in_log(self.get_reg_labels())

    def get_reg_vals(self) -> str:
        s = []
        for i in ['cp', 'cr', 'ac', 'br', 'sr', 'ir', '_or', 'ar', 'dr', 'sp']:
            s.append(hex(getattr(self.data_path, i))[2:].zfill(2))
        return ' | '.join(s).upper()

    def get_reg_and_tick_vals(self) -> str:
        return f'{self.cpu.tick:5} | {self.cpu.mc:3} | {self.get_reg_vals()}'

    @staticmethod
    def get_reg_labels() -> str:
        s = ['cp', 'cr', 'ac', 'br', 'sr', 'ir', 'or', 'ar', 'dr', 'sp']
        return ' - '.join(s).upper()

    @staticmethod
    def get_reg_labels_with_tick() -> str:
        s = [' tick', ' mc', 'cp', 'cr', 'ac', 'br', 'sr', 'ir', 'or', 'ar', 'dr', 'sp']
        return ' - '.join(s).upper()


class CPU:
    tick = 0
    mc = 0  # microcode pointer

    def __init__(
            self,
            logger: Logger,
            memory_filename: str = 'files/mem.bin',
            microcode_filename: str = 'files/microcode.bin',
            input_filename: str = 'files/input.txt',
            output_filename: str = 'files/output.txt'
    ):
        self.microcode_filename = microcode_filename
        self.input_file = InputFile(input_filename)
        self.output_filename = output_filename
        self.data_path = DataPath(memory_filename)
        self.logger = logger
        self.logger.bound(self.data_path, self)

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
        self.logger.log()
        while self.tick <= tick_limit and self.data_path.get_w_flag():
            self.try_to_read_out()
            self.try_to_write_inp()
            self.execute_instruction()
            self.tick += 1
            self.logger.log()

    def try_to_read_out(self):
        if self.data_path.is_o_flag_set() and self.mc == 0:
            with open(self.output_filename, 'a') as out:
                out.write(convert_from_ascii(self.data_path.reed_output()))

    def try_to_write_inp(self):
        if not self.data_path.is_i_flag_set() and self.input_file.has_next():
            self.data_path.write_input(self.input_file.get_symbol())
