"""Reads a backup file made by the Database page. The file is parsed, never executed as SQL.

Only the statements the backup itself creates are accepted: SET, DROP TABLE, CREATE TABLE and INSERT.
Values are converted to Python objects here and inserted later with parameterized queries.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any

from backend.core.exceptions import ValidationFailedError

_TOKEN = re.compile(
    r"""
      '(?:[^'\\]|\\.|'')*'          # string
    | "(?:[^"\\]|\\.|"")*"          # string (double quotes)
    | `(?:[^`]|``)*`                # identifier
    | --(?=[ \t\r\n]|$)[^\n]*       # comment
    | ;
    | [^'"`;-]+
    | -
    """,
    re.X | re.S,
)
_VALUE = re.compile(
    r"""\s*(?:
      (?P<hex>[Xx]'[0-9A-Fa-f]*')
    | (?P<str>'(?:[^'\\]|\\.|'')*')
    | (?P<null>NULL\b)
    | (?P<num>-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?)
    | (?P<punct>[(),])
    )""",
    re.X | re.S | re.I,
)
_SET_OK = re.compile(r"(?is)^SET\s+(NAMES\s+utf8mb4|FOREIGN_KEY_CHECKS\s*=\s*[01])$")
_DROP = re.compile(r"(?is)^DROP\s+TABLE\s+IF\s+EXISTS\s+`([^`]+)`$")
_CREATE = re.compile(r"(?is)^CREATE\s+TABLE\s+`([^`]+)`")
_INSERT = re.compile(r"(?is)^INSERT\s+INTO\s+`([^`]+)`\s*\(([^)]*)\)\s*VALUES\s*")
_ESCAPES = {"0": "\0", "n": "\n", "r": "\r", "t": "\t", "b": "\b", "Z": "\x1a"}


@dataclass
class ParsedBackup:
    """What the file contains: the tables it mentions and the rows to insert."""

    tables: set[str] = field(default_factory=set)
    inserts: list[tuple[str, list[str], list[list[Any]]]] = field(default_factory=list)


def _split(text: str) -> list[str]:
    """Split into statements at ';' (outside quotes) and drop comments."""
    statements: list[str] = []
    buffer: list[str] = []
    position = 0
    for match in _TOKEN.finditer(text):
        if match.start() != position:
            raise ValidationFailedError("The file could not be read (an unfinished quote or an unknown character).")
        position = match.end()
        token = match.group()
        if token == ";":
            statement = "".join(buffer).strip()
            if statement:
                statements.append(statement)
            buffer = []
        elif not token.startswith("--"):
            buffer.append(token)
    if position != len(text):
        raise ValidationFailedError("The file could not be read (an unfinished quote or an unknown character).")
    tail = "".join(buffer).strip()
    if tail:
        statements.append(tail)
    return statements


def _string(token: str) -> str:
    return re.sub(r"\\(.)|''", lambda m: _ESCAPES.get(m.group(1), m.group(1)) if m.group(1) is not None else "'", token[1:-1], flags=re.S)


def _rows(text: str, width: int, table: str) -> list[list[Any]]:
    """Turn "(1, 'a'), (2, NULL)" into [[1, 'a'], [2, None]]."""
    rows: list[list[Any]] = []
    row: list[Any] = []
    need = "open"  # what must come next: open, value, sep (comma or close), after (comma between rows)
    position = 0
    text = text.strip()
    bad = ValidationFailedError(f"The data for {table} is not in the expected backup format.")
    while position < len(text):
        match = _VALUE.match(text, position)
        if not match:
            raise bad
        position = match.end()
        kind = match.lastgroup
        if kind == "punct":
            mark = match.group("punct")
            if need == "open" and mark == "(":
                row, need = [], "value"
            elif need == "sep" and mark == ",":
                need = "value"
            elif need == "sep" and mark == ")":
                if len(row) != width:
                    raise ValidationFailedError(f"A row for {table} has {len(row)} values but {width} columns were listed.")
                rows.append(row)
                need = "after"
            elif need == "after" and mark == ",":
                need = "open"
            else:
                raise bad
            continue
        if need != "value":
            raise bad
        token = match.group(kind)
        if kind == "hex":
            row.append(bytes.fromhex(token[2:-1]))
        elif kind == "str":
            row.append(_string(token))
        elif kind == "null":
            row.append(None)
        else:
            row.append(int(token) if re.fullmatch(r"-?\d+", token) else Decimal(token))
        need = "sep"
    if need != "after":
        raise bad
    return rows


def parse_backup(content: str) -> ParsedBackup:
    """Validate and read a backup file. Raises ValidationFailedError when it is not one of ours."""
    text = content.lstrip("\ufeff")
    if "AppointMed database backup" not in text[:300]:
        raise ValidationFailedError("This is not an AppointMed backup. Use a file made by 'Create and download backup'.")
    parsed = ParsedBackup()
    for statement in _split(text):
        if _SET_OK.match(statement):
            continue
        drop, create, insert = _DROP.match(statement), _CREATE.match(statement), _INSERT.match(statement)
        if drop:
            parsed.tables.add(drop.group(1))
        elif create:
            parsed.tables.add(create.group(1))  # structure is not changed by an import
        elif insert:
            table = insert.group(1)
            columns = [c.strip().strip("`") for c in insert.group(2).split(",")]
            parsed.tables.add(table)
            parsed.inserts.append((table, columns, _rows(statement[insert.end():], len(columns), table)))
        else:
            raise ValidationFailedError(f"The file contains a statement that is not allowed: {statement[:40]}...")
    if not parsed.tables:
        raise ValidationFailedError("The file has no tables in it.")
    return parsed