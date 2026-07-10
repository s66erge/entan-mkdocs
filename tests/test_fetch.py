from unittest.mock import Mock, patch

from libs.fetch import (
    fetch_scrap,
    get_period_type,
    deduplicate,
    check_within,
    get_dhamma_courses_types,
)


# ----------------------------------------------------------------------
# get_period_type: maps a dhamma.org raw course type to a center period type
# ----------------------------------------------------------------------
def test_get_period_type_replace_all():
    replacement = [{"raw_course_type": "ABC", "course_description": "@ALL@", "period_type": "ALLTYPE"}]
    assert get_period_type("ABC", "anything", [], replacement) == "ALLTYPE"


def test_get_period_type_replace_by_cleaned_description():
    replacement = [{"raw_course_type": "DEF", "course_description": "Z", "period_type": "W"}]
    # course_type "Z-course" -> cleaned "ZCOURSE", which contains "Z"
    assert get_period_type("DEF", "Z-course", [], replacement) == "W"


def test_get_period_type_fallback_to_mapping():
    dhamma_types = [{"raw_course_type": "R1", "period_type": "PT1"}]
    assert get_period_type("R1", "anything", dhamma_types, []) == "PT1"


def test_get_period_type_unknown_returns_input():
    assert get_period_type("UNKNOWN", "anything", [], []) == "UNKNOWN"


# ----------------------------------------------------------------------
# deduplicate: adjacent rows with same date+type but different source -> "BOTH"
# ----------------------------------------------------------------------
def test_deduplicate_marks_both():
    merged = [
        {"start_date": "2023-01-01", "period_type": "A", "source": "center.ok.db"},
        {"start_date": "2023-01-01", "period_type": "A", "source": "dhamma.org"},
        {"start_date": "2023-01-02", "period_type": "B", "source": "dhamma.org"},
    ]
    result = deduplicate(merged)
    assert len(result) == 2
    assert result[0]["source"] == "BOTH"
    assert result[0]["period_type"] == "A"
    assert result[1]["period_type"] == "B"


def test_deduplicate_keeps_distinct_rows():
    merged = [
        {"start_date": "2023-01-01", "period_type": "A", "source": "dhamma.org"},
        {"start_date": "2023-01-05", "period_type": "B", "source": "dhamma.org"},
    ]
    result = deduplicate(merged)
    assert len(result) == 2
    assert [r["source"] for r in result] == ["dhamma.org", "dhamma.org"]


# ----------------------------------------------------------------------
# check_within: is this_row's start inside [row_aft.start, row_aft.end) ?
# ----------------------------------------------------------------------
def test_check_within_inside():
    this_row = {"start_date": "2023-01-03"}
    row_aft = {"start_date": "2023-01-01", "end_date": "2023-01-05"}
    assert check_within(this_row, row_aft) is True


def test_check_within_outside():
    this_row = {"start_date": "2023-01-06"}
    row_aft = {"start_date": "2023-01-01", "end_date": "2023-01-05"}
    assert check_within(this_row, row_aft) is False


# ----------------------------------------------------------------------
# get_dhamma_courses_types: strips trailing OSC and resolves period types
# ----------------------------------------------------------------------
def test_get_dhamma_courses_types_strips_osc_and_maps():
    extracted = [{
        "course_start_date": "2023-01-01",
        "course_end_date": "2023-01-11",
        "course_type_anchor": "TenDayOSC",
        "course_type": "CT",
    }]
    dhamma_types = [{"raw_course_type": "TenDay", "period_type": "PT10"}]
    result = get_dhamma_courses_types(extracted, center_obj=None,
                                      dhamma_types=dhamma_types, replacement=[])
    assert len(result) == 1
    assert result[0]["period_type"] == "PT10"
    assert result[0]["source"] == "dhamma.org"
    assert result[0]["start_date"] == "2023-01-01"


# ----------------------------------------------------------------------
# fetch_scrap: paginates dhamma.org and filters cancelled / non-center courses
# ----------------------------------------------------------------------
def _course(course_type):
    return {
        "course_start_date": "2023-01-01",
        "course_end_date": "2023-01-11",
        "raw_course_type": "10d",
        "course_type_anchor": "TenDay",
        "course_type": course_type,
        "location": {"center_noncenter": "center"},
        "status": [{"status": "OPEN"}],
    }


def test_fetch_scrap_paginates_and_maps():
    page1 = {"courses": [_course("CT1")], "pages": 2}
    page2 = {"courses": [_course("CT2")], "pages": 2}

    def fake_post(url, data=None, **kwargs):
        resp = Mock()
        resp.json.return_value = page1 if int(data["page"]) == 1 else page2
        return resp

    mock_session = Mock()
    mock_session.post.side_effect = fake_post
    with patch("libs.fetch.requests.Session", return_value=mock_session):
        result = fetch_scrap("location_1", "2023-01-01", "2023-02-01")

    assert [c["course_type"] for c in result] == ["CT1", "CT2"]


def test_fetch_scrap_filters_cancelled_and_noncenter():
    cancelled = _course("CANCELLED_ONE")
    cancelled["status"] = [{"status": "cancelled"}]
    noncenter = _course("NONCENTER_ONE")
    noncenter["location"] = {"center_noncenter": "noncenter"}
    payload = {"courses": [_course("KEPT"), cancelled, noncenter], "pages": 1}

    mock_session = Mock()
    mock_session.post.return_value = Mock(json=Mock(return_value=payload))
    with patch("libs.fetch.requests.Session", return_value=mock_session):
        result = fetch_scrap("location_1", "2023-01-01", "2023-02-01")

    assert [c["course_type"] for c in result] == ["KEPT"]
