def clean_memory(memory_filename: str = 'mem.bin'):
    with open(memory_filename, 'wb') as mem, open('files/mem.empty.bin', 'rb') as clean_mem:
        mem.write(clean_mem.read())
