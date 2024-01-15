from typing import List


def invert_bits(bits: int, length=8):
    """ Инвертирует биты и возвращает последовательность нужного размера """
    return (1 << length) - 1 - bits


def replace_bits(old_val: int, new_val: int, mask: int, length=8):
    """ Заменяет old_val[i] = new_val[i], где mask[i] = 1 """
    t = old_val & invert_bits(mask, length)
    t = t | (new_val & mask)
    return t


def join_bits(bits_array: List[int]):
    """ Соединяет переданный массив битов в одну последовательность.
        0 элемент массива является младшим разрядом """
    bits = 0
    for i in range(len(bits_array)):
        if bits_array[i] not in [0, 1]:
            raise TypeError('Допустимое значение элемента массива битов 0 или 1')
        bits += bits_array[i] << i
    return bits
