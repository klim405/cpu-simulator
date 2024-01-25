import argparse

from machine import CPU, Logger
from translator_asm import TranslatorASM
from utils.files import clean_memory


def main(asm: str, inp: str, out: str, mem: str, micro: str, log: str, log_mode: str, limit: int):
    clean_memory(mem)
    TranslatorASM(asm, mem).translate()
    cpu = CPU(Logger(log, log_mode), mem, micro, inp, out)
    cpu.start(tick_limit=limit)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('assembler')
    parser.add_argument('-i', '--input', default='files/input.txt')
    parser.add_argument('-o', '--output', default='files/temp/output.txt')
    parser.add_argument('-m', '--memory', default='files/temp/mem.bin')
    parser.add_argument('-c', '--microcode', default='files/microcode.bin')
    parser.add_argument('-l', '--log', default='files/temp/log.txt')
    parser.add_argument('-t', '--tick-lim', default=20000000000, type=int)
    parser.add_argument('--log-mode', default='instr')
    args = parser.parse_args()
    main(args.assembler, args.input, args.output, args.memory,
         args.microcode, args.log, args.log_mode, args.tick_lim)
