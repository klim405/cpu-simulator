import os
import tempfile

import pytest

from main import run_simulator


@pytest.mark.golden_test("golden/*.yml")
def test_translator_and_machine(golden, caplog):
    """
    Вход:

    - `script` -- исходный код
    - `input` -- данные на ввод процессора для симуляции

    Выход:

    - `out_code` -- машинный код, сгенерированный транслятором
    - `output` -- стандартный вывод транслятора и симулятора
    - `out_log` -- журнал программы
    """
    # Создаём временную папку для тестирования приложения.
    with tempfile.TemporaryDirectory() as tmpdirname:
        # Готовим имена файлов для входных и выходных данных.
        script = os.path.join(tmpdirname, "script.asm")
        input_stream = os.path.join(tmpdirname, "input.txt")
        memory = os.path.join(tmpdirname, "mem.bin")
        output = os.path.join(tmpdirname, "output.txt")
        out_log = os.path.join(tmpdirname, "log.txt")

        # Записываем входные данные в файлы. Данные берутся из yaml файлов теста.
        with open(script, "w", encoding="utf-8") as file:
            file.write(golden["script"])
        with open(input_stream, "w", encoding="utf-8") as file:
            file.write(golden["input"])

        # Запускаем транслятор и cpu
        run_simulator(script, input_stream, output, memory,
                      'files/microcode.bin', out_log, log_mode='instr', limit=200000)

        # Выходные данные считываем в переменные.
        output_data = ''
        if os.path.exists(output):
            with open(output, "r", encoding="utf-8") as output_file:
                output_data = output_file.read()

        with open(out_log, 'r', encoding="utf-8") as log_file:
            log_data = log_file.read()

        # Проверяем, что ожидания соответствуют реальности.
        assert output_data == golden.out["output"]
        assert log_data == golden.out["out_log"]
