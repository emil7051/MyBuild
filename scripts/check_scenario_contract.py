#!/usr/bin/env python3
"""Validate ScenarioKey parity between Python scenarios and TypeScript contracts."""

from __future__ import annotations

from pathlib import Path
import re
import sys
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from data.scenarios import SCENARIOS  # noqa: E402

SCENARIO_TYPE_FILE = REPO_ROOT / "shared/types/tco.types.ts"
SCENARIO_KEY_TYPE_PATTERN = re.compile(
    r"export\s+type\s+ScenarioKey\s*=\s*(.+?);", re.DOTALL
)
STRING_LITERAL_PATTERN = re.compile(r"'([^']+)'")


def extract_scenario_keys_from_ts_union(type_file: Path) -> list[str]:
    """Read ScenarioKey union literals from shared TypeScript types."""
    content = type_file.read_text(encoding="utf-8")
    match = SCENARIO_KEY_TYPE_PATTERN.search(content)
    if not match:
        raise ValueError(
            f"Could not find `ScenarioKey` union in {type_file.relative_to(REPO_ROOT)}"
        )

    keys = STRING_LITERAL_PATTERN.findall(match.group(1))
    if not keys:
        raise ValueError(
            f"`ScenarioKey` union in {type_file.relative_to(REPO_ROOT)} is empty"
        )
    return keys


def compare_keys(
    python_keys: Iterable[str], ts_keys: Sequence[str]
) -> tuple[list[str], list[str]]:
    """Return missing and extra keys compared to Python source of truth."""
    python_set = set(python_keys)
    ts_set = set(ts_keys)
    missing_in_ts = sorted(python_set - ts_set)
    extra_in_ts = sorted(ts_set - python_set)
    return missing_in_ts, extra_in_ts


def main() -> int:
    python_keys = sorted(SCENARIOS.keys())
    ts_keys = extract_scenario_keys_from_ts_union(SCENARIO_TYPE_FILE)

    missing_in_ts, extra_in_ts = compare_keys(python_keys, ts_keys)
    if missing_in_ts or extra_in_ts:
        print("ERROR: Scenario contract mismatch detected.")
        print(f"Python scenarios: {python_keys}")
        print(f"TypeScript ScenarioKey union: {sorted(set(ts_keys))}")
        if missing_in_ts:
            print(f"Missing in ScenarioKey union: {missing_in_ts}")
        if extra_in_ts:
            print(f"Extra keys in ScenarioKey union: {extra_in_ts}")
        print(
            "Update shared/types/tco.types.ts to match data.scenarios.SCENARIOS keys."
        )
        return 1

    print(
        f"Scenario contract check passed ({len(python_keys)} keys): {', '.join(python_keys)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
