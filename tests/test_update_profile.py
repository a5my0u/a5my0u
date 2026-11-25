import json
from pathlib import Path

import pytest

from scripts import update_profile as update
from test_snake import fixture_snapshot


def svg(label="valid"):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20"><title>{label}</title><rect width="20" height="20"/></svg>'


def file_set(label="valid"):
    return {
        "github-stats.svg": svg(label),
        "github-stats-mobile.svg": svg(label),
        "languages.svg": svg(label),
        "languages-mobile.svg": svg(label),
        "contribution-snake.svg": svg(label),
        "contribution-snake-mobile.svg": svg(label),
        "public-data.json": json.dumps(fixture_snapshot()),
    }


def test_invalid_late_svg_preserves_every_prior_asset(tmp_path):
    update.replace_set(tmp_path, file_set("previous"))
    old = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    changed = file_set("new")
    changed["contribution-snake.svg"] = "<svg>broken"
    with pytest.raises(Exception):
        update.replace_set(tmp_path, changed)
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == old


def test_io_failure_rolls_back_entire_local_set(tmp_path, monkeypatch):
    update.replace_set(tmp_path, file_set("previous"))
    old = {p.name: p.read_bytes() for p in tmp_path.iterdir()}
    real = update.os.replace
    count = 0
    def failing_replace(source, destination):
        nonlocal count
        count += 1
        if count == 2:
            raise OSError("fixture disk failure")
        return real(source, destination)
    monkeypatch.setattr(update.os, "replace", failing_replace)
    with pytest.raises(OSError):
        update.replace_set(tmp_path, file_set("new"))
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == old


def test_unchanged_set_does_not_touch_files(tmp_path):
    assert len(update.replace_set(tmp_path, file_set())) == 7
    before = {p.name: p.stat().st_mtime_ns for p in tmp_path.iterdir()}
    assert update.replace_set(tmp_path, file_set()) == []
    assert before == {p.name: p.stat().st_mtime_ns for p in tmp_path.iterdir()}


@pytest.mark.parametrize("payload", [
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><script/></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1"><image href="https://thirdparty.invalid/x"/></svg>',
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1 1" onload="alert(1)"/>',
    '<!DOCTYPE svg [<!ENTITY x SYSTEM "file:///etc/passwd">]><svg/>',
])
def test_rejects_active_or_external_svg_content(payload):
    with pytest.raises(ValueError):
        update.validate_svg(payload)


def test_missing_kpi_not_accepted_as_zero():
    data = fixture_snapshot()
    del data["kpis"]["commits"]
    with pytest.raises(ValueError, match="commits"):
        update.validate_snapshot(data)


def test_first_failure_placeholders_are_explicit_and_do_not_replace_existing(tmp_path):
    (tmp_path / "github-stats.svg").write_text(svg("known good"), encoding="utf-8")
    update.ensure_initial_placeholders(tmp_path)
    assert "known good" in (tmp_path / "github-stats.svg").read_text()
    assert "Awaiting verified public data" in (tmp_path / "languages.svg").read_text()
    assert not (tmp_path / "public-data.json").exists()


def test_snapshot_forbids_secret_or_private_metadata():
    data = fixture_snapshot()
    data["source"]["authorization"] = "fixture-secret"
    with pytest.raises(ValueError, match="non-public"):
        update.validate_snapshot(data)


def test_rejects_snapshot_from_a_different_user():
    with pytest.raises(ValueError, match="username"):
        update.render_set(fixture_snapshot(), {"username": "another-profile"})
