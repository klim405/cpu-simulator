import argparse


def str_to_byte(instruction: str) -> bytes:
    val = int(instruction, base=2)
    return val.to_bytes(5, 'big')


def dump(src: str, dest: str):
    with open(dest, 'wb') as dest, open(src, 'r') as src:
        for line in src.readlines():
            if line:
                dest.write(str_to_byte(line.strip()))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--source', default='files/microcode.txt')
    parser.add_argument('-t', '--target', default='files/microcode.bin')
    args = parser.parse_args()
    dump(args.source, args.target)


if __name__ == '__main__':
    main()
