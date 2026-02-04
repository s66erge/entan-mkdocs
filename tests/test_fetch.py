import json
import types
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch

import pytest

from libs.fetch import (
    get_field_from_db,
    fetch_courses_from_dhamma,
    get_period_type,
    deduplicate,
    check_row,
    check_plan,
)


# ----------------------------------------------------------------------
# Helpers / Fixtures
# ----------------------------------------------------------------------
class DummyCenter:
    """Simple object with attribute access."""
    def __init__(self, location=None, **extra):
        self.location = location
        for k, v in extra.items():
            setattr(self, k, v)


class DummyCenters:
    """Mimic the .t.centers mapping used in get_field_from_db."""
    def __init__(self, mapping):
        self._mapping = mapping

    def __getitem__(self, key):
        return self._mapping[key]


class DummyDBCentral:
    """Mimic the db_central with .t.centers."""
    def __init__(self, centers):
        self.t = types.SimpleNamespace(centers=DummyCenters(centers))


# ----------------------------------------------------------------------
# Tests for get_field_from_db
# ----------------------------------------------------------------------
def test_get_field_from_db_location():
    db = DummyDBCentral({"C1": DummyCenter(location="NY")})
    assert get_field_from_db(db, "C1", "location") == "location_NY"


def test_get_field_from_db_other_json():
    db = DummyDBCentral({"C1": DummyCenter(other='{"a": 1, "b": 2}')})
    # The function uses json.loads on the attribute value
    result = get_field_from_db(db, "C1", "other")
    assert result == {"a": 1, "b": 2}


# ----------------------------------------------------------------------
# Tests for fetch_courses_from_dhamma (pagination handling)
# ----------------------------------------------------------------------
def test_fetch_courses_from_dhamma_pagination():
    # Mock the requests.post to simulate two pages
    page1 = {
        "courses": [{"course_type": "CT1"}],
        "pages": 2
    }
    page2 = {
        "courses": [{"course_type": "CT2"}],
        "pages": 2
    }

    def fake_post(url, data=None, headers=None, timeout=None):
        page = int(data["page"])
        resp = Mock()
        resp.json.return_value = page1 if page == 1 else page2
        resp.raise_for_status = Mock()
        return resp

    with patch("libs.fetch.requests.post", side_effect=fake_post):
        result = fetch_courses_from_dhamma("loc", "2023-01-01", "2023-02-01")
        # Two courses from both pages
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["course_type"] == "CT1"
        assert result[1]["course_type"] == "CT2"


# ----------------------------------------------------------------------
# Tests for get_period_type
# ----------------------------------------------------------------------
def test_get_period_type_replacements():
    other = {"replacements": {"ABC": {"@ALL@": "ALLTYPE"},
                                "DEF": {"Z": "W"}}}
    list_of = [{"raw_course_type": "R1", "period_type": "PT1"}]

    # Exact replacement via @ALL@
    assert get_period_type("ABC", "any", list_of, other) == "ALLTYPE"
    # Replacement via key X -> Y
    assert get_period_type("DEF", "Z", list_of, other) == "W"
    # Fallback to list_of
    assert get_period_type("R1", "any", list_of, other) == "PT1"
    # Unknown
    assert get_period_type("UNKNOWN", "any", list_of, other) == "UNKNOWN UNKNOWN"


# ----------------------------------------------------------------------
# Tests for deduplicate
# ----------------------------------------------------------------------
def test_deduplicate_basic():
    merged = [
        {"start_date": "2023-01-01", "period_type": "A", "source": "s1"},
        {"start_date": "2023-01-01", "period_type": "A", "source": "s2"},
        {"start_date": "2023-01-02", "period_type": "B", "source": "s3"},
    ]
    result = deduplicate(merged, del_as_BETWEEN=[])
    # First two should merge into one with source "BOTH"
    assert result[0]["source"] == "BOTH"
    assert result[0]["start_date"] == "2023-01-01"
    assert result[0]["period_type"] == "A"
    # Second entry unchanged
    assert result[1]["period_type"] == "B"


# ----------------------------------------------------------------------
# Tests for check_row and check_plan
# ----------------------------------------------------------------------
def test_check_row_gap():
    row = {"period_type": "type1", "start_date": "2023-01-01"}
    # next start is 2023-01-04, duration=2 => gap of 2 days expected
    checked = check_row(row, next_type="type2", next_start_date="2023-01-05",
                        previous_type=None, previous_end_date=None,
                        types_with_duration=[{
                            "valid_types": "type1",
                            "duration": 2,
                            "var_period": False,
                            "over_oth": []
                        }])
    assert checked["check"] == "GAP of 2"


def test_check_plan_no_valid_types():
    # Minimal dummy db_center with periods_struct returning empty list
    class DummyPeriodsStruct:
        def __call__(self):
            return []  # no period definitions

    class DummyT:
        def __init__(self):
            self.periods_struct = DummyPeriodsStruct()

    class DummyDB:
        def __init__(self):
            self.t = DummyT()

    db_center = DummyDB()
    other_course = {"variable-len": [], "override": {}}
    plan = [
        {"period_type": "X", "start_date": "2023-01-01"},
        {"period_type": "Y", "start_date": "2023-01-05"},
    ]
    # Should not raise; each entry gets a 'check' of "NoType"
    result = check_plan(plan, db_center, other_course)
    for item in result:
        assert item["check"] == "NoType"
