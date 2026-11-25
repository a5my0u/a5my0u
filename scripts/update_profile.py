"""Fetch and render a consistent asset set; retain known-good files on failure."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import tempfile
import xml.etree.ElementTree as ET

try:
    from .fetch_github_data import fetch_data
    from . import generate_stats, generate_languages, generate_snake
except ImportError:
    from fetch_github_data import fetch_data
    import generate_stats
    import generate_languages
    import generate_snake


ASSET_NAMES = ("github-stats.svg", "github-stats-mobile.svg", "languages.svg", "languages-mobile.svg", "contribution-snake.svg", "contribution-snake-mobile.svg", "public-data.json")


def validate_svg(value: str) -> None:
    if "<!DOCTYPE" in value.upper() or "<!ENTITY" in value.upper():
        raise ValueError("SVG external entities are forbidden")
    root = ET.fromstring(value)
    if root.tag != "{http://www.w3.org/2000/svg}svg":
        raise ValueError("Output must be a namespaced SVG document")
    if not root.get("viewBox"):
        raise ValueError("SVG must define an aspect-preserving viewBox")
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] in {"script", "foreignObject", "iframe"}:
            raise ValueError("SVG executable or foreign content is forbidden")
        for key, val in element.attrib.items():
            if key.lower().startswith("on"):
                raise ValueError("SVG event handlers are forbidden")
            if key.rsplit("}", 1)[-1] == "href" and not val.startswith("#"):
                raise ValueError("Generated SVG cannot load external content")


def validate_snapshot(data: dict) -> None:
    if data.get("schema_version") != 1 or data.get("scope", {}).get("public_only") is not True:
        raise ValueError("A versioned, explicitly public-only snapshot is required")
    for name in ("commits", "pull_requests", "issues", "stars"):
        value = data.get("kpis", {}).get(name)
        if type(value) is not int or value < 0:
            raise ValueError(f"Missing or invalid KPI: {name}")
    languages = data.get("languages")
    if not isinstance(languages, dict):
        raise ValueError("Language byte totals are missing")
    if any(not isinstance(k, str) or type(v) is not int or v < 0 for k, v in languages.items()):
        raise ValueError("Language byte totals must be non-negative integers")
    generate_snake.validated_days(data)
    # Store only this public, aggregate schema. Do not preserve arbitrary API data.
    forbidden = {"token", "authorization", "email", "private_repositories", "private_contributions"}
    def scan(value):
        if isinstance(value, dict):
            for key, nested in value.items():
                if key.lower() in forbidden:
                    raise ValueError("Snapshot contains a non-public field")
                scan(nested)
        elif isinstance(value, list):
            for nested in value:
                scan(nested)
    scan(data)


def public_snapshot(data: dict) -> dict:
    """Keep only fields explicitly used by the public renderers."""
    keys = ("schema_version", "username", "as_of", "start_date", "end_date", "scope", "kpis", "languages", "contributions", "repositories", "source")
    return {key: data[key] for key in keys if key in data}


def replace_set(output: Path, files: dict[str, str]) -> list[str]:
    """Validate first, stage all, then replace with rollback on local I/O errors.

    Remote publishing is a separate single-ref transaction, so a killed local
    process can never publish a partial generation.
    """
    if set(files) != set(ASSET_NAMES):
        raise ValueError("Refusing an incomplete generated asset set")
    for name in ASSET_NAMES:
        if name.endswith(".svg"):
            validate_svg(files[name])
    validate_snapshot(json.loads(files["public-data.json"]))
    output.mkdir(parents=True, exist_ok=True)
    changed = [name for name in ASSET_NAMES if not (output / name).exists() or (output / name).read_text(encoding="utf-8") != files[name]]
    if not changed:
        return []
    with tempfile.TemporaryDirectory(prefix="profile-stage-", dir=output.parent) as temp:
        stage = Path(temp)
        prior: dict[str, bytes | None] = {}
        for name in changed:
            (stage / name).write_text(files[name], encoding="utf-8", newline="\n")
            prior[name] = (output / name).read_bytes() if (output / name).exists() else None
        done = []
        try:
            for name in changed:
                os.replace(stage / name, output / name)
                done.append(name)
        except OSError:
            for name in reversed(done):
                if prior[name] is None:
                    (output / name).unlink(missing_ok=True)
                else:
                    (output / name).write_bytes(prior[name])
            raise
    return changed


def render_set(snapshot: dict, config: dict) -> dict[str, str]:
    validate_snapshot(snapshot)
    if snapshot.get("username", "").casefold() != config["username"].casefold():
        raise ValueError("Snapshot username does not match the configured profile")
    return {
        "github-stats.svg": generate_stats.render(snapshot, config),
        "github-stats-mobile.svg": generate_stats.render_mobile(snapshot, config),
        "languages.svg": generate_languages.render(snapshot, config),
        "languages-mobile.svg": generate_languages.render_mobile(snapshot, config),
        "contribution-snake.svg": generate_snake.render(snapshot, config),
        "contribution-snake-mobile.svg": generate_snake.render(snapshot, config, mobile=True),
        "public-data.json": json.dumps(public_snapshot(snapshot), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    }


def ensure_initial_placeholders(output: Path) -> None:
    """Prevent broken initial README images without inventing numeric data.

    These explicit, non-numeric placeholders are never sent to the generated
    branch: the CLI exits unsuccessfully and no valid public-data.json exists.
    Existing files, including any previous real data, are never overwritten.
    """
    output.mkdir(parents=True, exist_ok=True)
    value = '''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="240" viewBox="0 0 960 240" role="img" aria-labelledby="pending-title">
<title id="pending-title">Awaiting verified public data</title>
<rect x="1" y="1" width="958" height="238" rx="18" fill="#171717" stroke="#303030"/>
<text x="48" y="105" fill="#F5F5F5" font-family="Arial,sans-serif" font-size="30">Awaiting verified public data</text>
<text x="48" y="151" fill="#A1A1AA" font-family="Arial,sans-serif" font-size="20">No statistics are shown until a complete API update succeeds.</text>
</svg>
'''
    validate_svg(value)
    for name in ASSET_NAMES:
        if name.endswith(".svg") and not (output / name).exists():
            try:
                with (output / name).open("x", encoding="utf-8", newline="\n") as stream:
                    stream.write(value)
            except FileExistsError:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("config/profile.json"))
    parser.add_argument("--snapshot", type=Path, help="Render an already verified public snapshot without networking")
    parser.add_argument("--as-of", help="End date for reproducible public data acquisition")
    parser.add_argument("--output", type=Path, default=Path("assets/generated"))
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        data = json.loads(args.snapshot.read_text(encoding="utf-8")) if args.snapshot else fetch_data(config, as_of=args.as_of)
        changed = replace_set(args.output, render_set(data, config))
    except Exception as exc:
        # Exceptions may include remote payloads; never print them or credentials.
        try:
            ensure_initial_placeholders(args.output)
        except OSError:
            pass
        print(f"Profile update failed ({type(exc).__name__}). Existing generated assets were retained.")
        return 1
    print("Generated assets updated." if changed else "Generated assets unchanged; no write needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
