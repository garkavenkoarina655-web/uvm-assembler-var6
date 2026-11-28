#!/usr/bin/env python3
"""
Ассемблер учебной виртуальной машины (УВМ), вариант №6.
Этап 1: разбор JSON-программы и трансляция в промежуточное представление.
"""

import argparse
import json
import sys
from typing import Any


# Описание команд УВМ (вариант 6)
OPCODES = {
    "load_const": 2,   # Загрузка константы
    "load_mem": 14,    # Чтение значения из памяти
    "store_mem": 6,    # Запись значения в память
    "lt": 11,          # Бинарная операция "<"
}


def parse_program(source: str) -> list[dict[str, Any]]:
    """
    Разбирает JSON-программу и возвращает промежуточное представление.
    Каждая команда — словарь с полями A, B, C, ... и именем операции.
    """
    try:
        data = json.loads(source)
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка разбора JSON: {e}") from e

    if not isinstance(data, list):
        raise ValueError("Программа должна быть JSON-массивом команд")

    intermediate: list[dict[str, Any]] = []

    for i, instr in enumerate(data):
        if not isinstance(instr, dict):
            raise ValueError(f"Команда #{i} должна быть объектом")

        op_name = instr.get("op")
        if op_name not in OPCODES:
            raise ValueError(
                f"Неизвестная операция '{op_name}' в команде #{i}. "
                f"Допустимые: {', '.join(OPCODES.keys())}"
            )

        a = OPCODES[op_name]
        fields: dict[str, Any] = {"A": a, "op": op_name}

        if op_name == "load_const":
            # A=2, B=const (12 бит), C=addr (24 бит)
            if "const" not in instr or "addr" not in instr:
                raise ValueError(f"load_const требует поля 'const' и 'addr' (команда #{i})")
            fields["B"] = int(instr["const"])
            fields["C"] = int(instr["addr"])

        elif op_name == "load_mem":
            # A=14, B=addr (24 бит), C=offset (16 бит), D=addr (24 бит)
            for key in ("addr_src", "offset", "addr_dst"):
                if key not in instr:
                    raise ValueError(f"load_mem требует поле '{key}' (команда #{i})")
            fields["B"] = int(instr["addr_src"])
            fields["C"] = int(instr["offset"])
            fields["D"] = int(instr["addr_dst"])

        elif op_name == "store_mem":
            # A=6, B=addr (24 бит), C=addr (24 бит)
            for key in ("addr_ptr", "addr_src"):
                if key not in instr:
                    raise ValueError(f"store_mem требует поле '{key}' (команда #{i})")
            fields["B"] = int(instr["addr_ptr"])
            fields["C"] = int(instr["addr_src"])

        elif op_name == "lt":
            # A=11, B=offset (16 бит), C=addr (24 бит), D=addr (24 бит), E=addr (24 бит)
            for key in ("offset", "addr_left", "addr_dst", "addr_right_base"):
                if key not in instr:
                    raise ValueError(f"lt требует поле '{key}' (команда #{i})")
            fields["B"] = int(instr["offset"])
            fields["C"] = int(instr["addr_left"])
            fields["D"] = int(instr["addr_dst"])
            fields["E"] = int(instr["addr_right_base"])

        intermediate.append(fields)

    return intermediate


def print_intermediate(program: list[dict[str, Any]]) -> None:
    """
    Выводит промежуточное представление в формате полей и значений
    (как в тестах спецификации УВМ).
    """
    for instr in program:
        op = instr["op"]
        if op == "load_const":
            print(f"A={instr['A']}, B={instr['B']}, C={instr['C']}")
        elif op == "load_mem":
            print(f"A={instr['A']}, B={instr['B']}, C={instr['C']}, D={instr['D']}")
        elif op == "store_mem":
            print(f"A={instr['A']}, B={instr['B']}, C={instr['C']}")
        elif op == "lt":
            print(
                f"A={instr['A']}, B={instr['B']}, C={instr['C']}, "
                f"D={instr['D']}, E={instr['E']}"
            )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ассемблер УВМ (вариант 6). Этап 1 — промежуточное представление."
    )
    parser.add_argument("source", help="Путь к исходному файлу (JSON)")
    parser.add_argument("output", help="Путь к двоичному файлу-результату (пока не используется)")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Режим тестирования: вывести промежуточное представление",
    )
    args = parser.parse_args()

    try:
        with open(args.source, encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(f"Ошибка чтения файла {args.source}: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        program = parse_program(source)
    except ValueError as e:
        print(f"Ошибка трансляции: {e}", file=sys.stderr)
        sys.exit(1)

    if args.test:
        print_intermediate(program)
    else:
        # На этапе 1 двоичный файл ещё не формируем
        print(f"Промежуточное представление: {len(program)} команд(ы)")
        with open(args.output, "wb") as f:
            pass


if __name__ == "__main__":
    main()
