import sys


def byte_to_string(byte: bytes) -> str:
    val = int.from_bytes(byte, byteorder='big', signed=False)
    return bin(val)[2:].zfill(8)


def _bin(b: int, size=8) -> str:
    return bin(b)[2:].zfill(size)


def mem_to_text(mem_filename='files/mem.bin', start_addr=0, end_addr=0x10000, out=sys.stdout):
    with open(mem_filename, 'rb') as mem:
        mem.seek(start_addr)
        for i in range(end_addr - start_addr):
            print(_bin(start_addr + i), byte_to_string(mem.read(1)), sep=': ', file=out)


def text_to_mem(mem_filename='files/mem'):
    pass