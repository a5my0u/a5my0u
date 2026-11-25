from datetime import date, timedelta
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from scripts.generate_snake import render, route_points, validated_days


def fixture_snapshot(counts=(0, 1, 4, 0, 2, 0, 0, 3)):
    start = date(2026, 1, 1)
    return {
        "schema_version": 1,
        "username": "fixture-only-user",
        "as_of": (start + timedelta(days=len(counts) - 1)).isoformat(),
        "start_date": start.isoformat(),
        "end_date": (start + timedelta(days=len(counts) - 1)).isoformat(),
        "scope": {"public_only": True},
        "kpis": {"commits": sum(counts), "pull_requests": 0, "issues": 0, "stars": 0},
        "languages": {"Python": 100},
        "contributions": [{"date": (start + timedelta(days=i)).isoformat(), "count": count} for i, count in enumerate(counts)],
        "repositories": [],
        "source": {"fixture": True},
    }


@pytest.fixture
def config():
    return json.loads((Path(__file__).parents[1] / "config/profile.json").read_text(encoding="utf-8"))


def test_rejects_missing_days_instead_of_inventing_zero():
    data = fixture_snapshot()
    data["contributions"].pop(3)
    with pytest.raises(ValueError, match="Missing"):
        validated_days(data)


@pytest.mark.parametrize("count", [None, -1, True, 1.5, "2"])
def test_rejects_unknown_or_invalid_count(count):
    data = fixture_snapshot()
    data["contributions"][0]["count"] = count
    with pytest.raises(ValueError):
        validated_days(data)


def test_rejects_private_mixed_calendar():
    data = fixture_snapshot()
    data["scope"]["public_only"] = False
    with pytest.raises(ValueError, match="public-only"):
        validated_days(data)


def test_rejects_duplicate_and_out_of_range_dates():
    data = fixture_snapshot()
    data["contributions"][1]["date"] = data["contributions"][0]["date"]
    with pytest.raises(ValueError, match="Duplicate"):
        validated_days(data)


def test_route_uses_only_adjacent_unique_calendar_cells():
    route = route_points(53, 32, 76, 16)
    assert len(route) == len(set(route)) == 371
    for (x1, y1), (x2, y2) in zip(route, route[1:]):
        assert abs(x2 - x1) + abs(y2 - y1) == 16


def test_svg_is_deterministic_contains_real_counts_and_reduced_motion(config):
    data = fixture_snapshot()
    first = render(data, config)
    assert first == render(data, config)
    doc = ET.fromstring(first)
    assert doc.get("viewBox") == "0 0 960 226"
    assert "2026-01-03: 4 public activity events" in first
    assert "10 events" in first
    assert "#FBBF24" in first
    assert "prefers-reduced-motion" in first
    assert "@keyframes eat" in first
    assert "<script" not in first


def test_true_zero_calendar_keeps_zero_cells_and_animated_snake(config):
    result = render(fixture_snapshot((0, 0, 0)), config)
    assert "0 events" in result
    assert "@keyframes eat" not in result
    assert "@keyframes travel" in result


def test_svg_escapes_text_without_scripts(config):
    data = fixture_snapshot()
    data["username"] = '<script>alert("fixture")</script>'
    result = render(data, config)
    assert "<script" not in result


def test_mobile_calendar_keeps_every_real_day_and_count(config):
    data = fixture_snapshot(tuple(i % 5 for i in range(365)))
    result = render(data, config, mobile=True)
    doc = ET.fromstring(result)
    assert doc.get("width") == "320"
    titles = [node.text for node in doc.iter("{http://www.w3.org/2000/svg}title")]
    assert len([label for label in titles if "public activity events" in label]) == 365
    for day in data["contributions"]:
        assert f'{day["date"]}: {day["count"]} public activity events' in titles
    assert result == render(data, config, mobile=True)
