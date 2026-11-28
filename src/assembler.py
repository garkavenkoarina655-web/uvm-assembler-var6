#!/usr/bin/env python3
"""Ассемблер учебной виртуальной машины (УВМ), вариант №6.

Этапы 1-2: разбор JSON, промежуточное представление,
формирование машинного кода.
"""

import argparse
import json
import sys
from typing import Any


OPCODES = {
    "load_const": 2,
    "load_mem": 14,
    "store_mem": 6,
    "lt": 11,
}


def parse_program(source: str) -> list[dict[str, Any]]:
    """Разбирает JSON-программу в промежуточное представление.

    Каждая команда становится словарём с полями A, B, C и т.д.

    Args:
        source: Текст исходной программы в формате JSON.

    Returns:
        Список словарей — промежуточное представление.

    Raises:
        ValueError: При ошибке разбора или неизвестной команде.
    """
    try:
        data = json.loads(source)
    except json.JSONDecodeError as e:
        raise ValueError(f"Ошибка разбора JSON: {e}") from e

    if not isinstance(data, list):
        raise ValueError(
            "Программа должна быть JSON-массивом команд"
        )

    intermediate: list[dict[str, Any]] = []

    for i, instr in enumerate(data):
        if not isinstance(instr, dict):
            raise ValueError(
                f"Команда #{i} должна быть объектом"
            )

        op_name = instr.get("op")
        if op_name not in OPCODES:
            allowed = ", ".join(OPCODES.keys())
            raise ValueError(
                f"Неизвестная операция '{op_name}' "
                f"в команде #{i}. Допустимые: {allowed}"
            )

        fields = _build_fields(op_name, instr, i)
        intermediate.append(fields)

    return intermediate


def _build_fields(
    op_name: str, instr: dict[str, Any], index: int
) -> dict[str, Any]:
    """Собирает словарь полей для одной команды.

    Args:
        op_name: Имя операции.
        instr: Исходный объект команды из JSON.
        index: Номер команды (для сообщений об ошибках).

    Returns:
        Словарь с полями A, op и операндами.
    """
    a = OPCODES[op_name]
    fields: dict[str, Any] = {"A": a, "op": op_name}

    if op_name == "load_const":
        _require_keys(instr, ("const", "addr"), index)
        fields["B"] = int(instr["const"])
        fields["C"] = int(instr["addr"])

    elif op_name == "load_mem":
        keys = ("addr_src", "offset", "addr_dst")
        _require_keys(instr, keys, index)
        fields["B"] = int(instr["addr_src"])
        fields["C"] = int(instr["offset"])
        fields["D"] = int(instr["addr_dst"])

    elif op_name == "store_mem":
        keys = ("addr_ptr", "addr_src")
        _require_keys(instr, keys, index)
        fields["B"] = int(instr["addr_ptr"])
        fields["C"] = int(instr["addr_src"])

    elif op_name == "lt":
        keys = (
            "offset",
            "addr_left",
            "addr_dst",
            "addr_right_base",
        )
        _require_keys(instr, keys, index)
        fields["B"] = int(instr["offset"])
        fields["C"] = int(instr["addr_left"])
        fields["D"] = int(instr["addr_dst"])
        fields["E"] = int(instr["addr_right_base"])

    return fields


def _require_keys(
    instr: dict[str, Any],
    keys: tuple[str, ...],
    index: int,
) -> None:
    """Проверяет наличие обязательных полей в команде.

    Args:
        instr: Объект команды.
        keys: Кортеж обязательных ключей.
        index: Номер команды.

    Raises:
        ValueError: Если какое-то поле отсутствует.
    """
    for key in keys:
        if key not in instr:
            raise ValueError(
                f"Команда #{index}: отсутствует поле '{key}'"
            )


def encode_instruction(instr: dict[str, Any]) -> bytes:
    """Кодирует одну команду в машинный код.

    Поля упаковываются от младших бит к старшим.
    Результат — little-endian последовательность байт.

    Args:
        instr: Команда в промежуточном представлении.

    Returns:
        Байты машинной команды.
    """
    op = instr["op"]
    a = instr["A"]

    if op == "load_const":
        return _encode_load_const(a, instr)
    if op == "load_mem":
        return _encode_load_mem(a, instr)
    if op == "store_mem":
        return _encode_store_mem(a, instr)
    if op == "lt":
        return _encode_lt(a, instr)

    raise ValueError(f"Неизвестная операция: {op}")


def _encode_load_const(
    a: int, instr: dict[str, Any]
) -> bytes:
    """Кодирует load_const (5 байт).

    Биты: A(4) | B(12) | C(24).
    """
    b = instr["B"] & 0xFFF
    c = instr["C"] & 0xFFFFFF
    val = (a & 0xF) | (b << 4) | (c << 16)
    return val.to_bytes(5, byteorder="little")


def _encode_load_mem(
    a: int, instr: dict[str, Any]
) -> bytes:
    """Кодирует load_mem (9 байт).

    Биты: A(4) | B(24) | C(16) | D(24).
    """
    b = instr["B"] & 0xFFFFFF
    c = instr["C"] & 0xFFFF
    d = instr["D"] & 0xFFFFFF
    val = (
        (a & 0xF)
        | (b << 4)
        | (c << 28)
        | (d << 44)
    )
    return val.to_bytes(9, byteorder="little")


def _encode_store_mem(
    a: int, instr: dict[str, Any]
) -> bytes:
    """Кодирует store_mem (7 байт).

    Биты: A(4) | B(24) | C(24).
    """
    b = instr["B"] & 0xFFFFFF
    c = instr["C"] & 0xFFFFFF
    val = (a & 0xF) | (b << 4) | (c << 28)
    return val.to_bytes(7, byteorder="little")


def _encode_lt(a: int, instr: dict[str, Any]) -> bytes:
    """Кодирует lt (12 байт).

    Биты: A(4) | B(16) | C(24) | D(24) | E(24).
    """
    b = instr["B"] & 0xFFFF
    c = instr["C"] & 0xFFFFFF
    d = instr["D"] & 0xFFFFFF
    e = instr["E"] & 0xFFFFFF
    val = (
        (a & 0xF)
        | (b << 4)
        | (c << 20)
        | (d << 44)
        | (e << 68)
    )
    return val.to_bytes(12, byteorder="little")


def assemble(program: list[dict[str, Any]]) -> bytes:
    """Собирает программу в один байтовый поток.

    Args:
        program: Список команд в промежуточном виде.

    Returns:
        Полный машинный код программы.
    """
    result = bytearray()
    for instr in program:
        result.extend(encode_instruction(instr))
    return bytes(result)


def print_bytes(data: bytes) -> None:
    """Выводит байты в формате спецификации УВМ.

    Args:
        data: Машинный код.
    """
    hex_list = [f"0x{b:02X}" for b in data]
    print(", ".join(hex_list))


def main() -> None:
    """Точка входа CLI-приложения ассемблера."""
    parser = argparse.ArgumentParser(
        description="Ассемблер УВМ (вариант 6)"
    )
    parser.add_argument(
        "source",
        help="Путь к исходному файлу (JSON)",
    )
    parser.add_argument(
        "output",
        help="Путь к двоичному файлу-результату",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Вывести байты машинного кода",
    )
    args = parser.parse_args()

    try:
        with open(args.source, encoding="utf-8") as f:
            source = f.read()
    except OSError as e:
        print(
            f"Ошибка чтения {args.source}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        program = parse_program(source)
        binary = assemble(program)
    except ValueError as e:
        print(
            f"Ошибка трансляции: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        with open(args.output, "wb") as f:
            f.write(binary)
    except OSError as e:
        print(
            f"Ошибка записи {args.output}: {e}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"Размер двоичного файла: {len(binary)} байт")

    if args.test:
        print_bytes(binary)


if __name__ == "__main__":
    main()
