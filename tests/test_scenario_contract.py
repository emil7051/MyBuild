from data.scenarios import SCENARIOS
from scripts.check_scenario_contract import (
    SCENARIO_TYPE_FILE,
    compare_keys,
    extract_scenario_keys_from_ts_union,
)


def test_scenario_contract_keys_match() -> None:
    ts_keys = extract_scenario_keys_from_ts_union(SCENARIO_TYPE_FILE)
    missing_in_ts, extra_in_ts = compare_keys(SCENARIOS.keys(), ts_keys)

    assert missing_in_ts == []
    assert extra_in_ts == []
