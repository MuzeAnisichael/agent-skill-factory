"""Read-only CSV contract checks; exit 0 pass, 1 findings, 2 invalid input."""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from pathlib import Path


def check_csv(path: Path, required: list[str], numeric: list[str], unique: list[str], delimiter: str) -> dict:
    if len(delimiter) != 1:
        raise ValueError("delimiter must be one character")
    issues: list[dict] = []
    issue_count = 0

    def record(row: int, column: str, code: str) -> None:
        nonlocal issue_count
        issue_count += 1
        if len(issues) < 25:
            issues.append({"row": row, "column": column, "code": code})

    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, delimiter=delimiter, strict=True)
        columns = next(reader, None)
        if not columns or any(not column.strip() for column in columns) or len(set(columns)) != len(columns):
            raise ValueError("header must contain unique, non-empty column names")
        missing = sorted(set(required + numeric + unique) - set(columns))
        if missing:
            raise ValueError(f"declared columns not found: {', '.join(missing)}")
        seen = {column: set() for column in unique}
        row_count = 0
        empty_cell_count = 0
        for values in reader:
            if not values:
                continue
            row_count += 1
            row_number = reader.line_num
            if len(values) != len(columns):
                record(row_number, "", "row.width")
                continue
            cells = {column: value.strip() for column, value in zip(columns, values)}
            empty_cell_count += sum(not value for value in cells.values())
            for column in dict.fromkeys(required):
                if not cells[column]:
                    record(row_number, column, "required.empty")
            for column in dict.fromkeys(numeric):
                try:
                    valid = math.isfinite(float(cells[column]))
                except ValueError:
                    valid = False
                if not valid:
                    record(row_number, column, "numeric.invalid")
            for column, known in seen.items():
                value = cells[column]
                if not value:
                    continue
                if value in known:
                    record(row_number, column, "unique.duplicate")
                known.add(value)
    return {"passed": issue_count == 0, "columns": columns, "row_count": row_count,
            "empty_cell_count": empty_cell_count, "issue_count": issue_count, "issues": issues}


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a declared CSV contract without modifying input.")
    parser.add_argument("path", type=Path)
    parser.add_argument("--required", action="append", default=[])
    parser.add_argument("--numeric", action="append", default=[])
    parser.add_argument("--unique", action="append", default=[])
    parser.add_argument("--delimiter", default=",")
    args = parser.parse_args()
    try:
        report = check_csv(args.path, args.required, args.numeric, args.unique, args.delimiter)
    except (OSError, UnicodeError, ValueError, csv.Error) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
