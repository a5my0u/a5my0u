"""Render a deterministic, public-activity-only contribution snake.

This is an original SVG renderer, not a copy of Platane/snk. The source is the
same explicitly scoped REST snapshot as the KPI cards, never a private-mixed
GitHub contribution-calendar aggregate.
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from html import escape
import json
import math
from pathlib import Path


def validated_days(snapshot: dict) -> list[tuple[date, int]]:
    if snapshot.get("scope", {}).get("public_only") is not True:
        raise ValueError("Snake input must be explicitly public-only")
    start = date.fromisoformat(snapshot["start_date"])
    end = date.fromisoformat(snapshot["end_date"])
    length = (end - start).days + 1
    if not 1 <= length <= 366:
        raise ValueError("Snake interval must contain 1–366 days")
    values: dict[date, int] = {}
    for item in snapshot["contributions"]:
        day = date.fromisoformat(item["date"])
        count = item["count"]
        if type(count) is not int or count < 0:
            raise ValueError("A daily count must be a non-negative integer")
        if day in values or day < start or day > end:
            raise ValueError("Duplicate or out-of-range contribution day")
        values[day] = count
    expected = [start + timedelta(days=i) for i in range(length)]
    if set(values) != set(expected):
        raise ValueError("Missing contribution days must not become zero")
    return [(day, values[day]) for day in expected]


def route_points(columns: int, x0: float, y0: float, pitch: float) -> list[tuple[float, float]]:
    """A non-intersecting, adjacent-cell traversal with no random movement."""
    result = []
    for column in range(columns):
        rows = range(7) if column % 2 == 0 else range(6, -1, -1)
        result.extend((x0 + column * pitch, y0 + row * pitch) for row in rows)
    return result


def level_for(count: int, maximum: int) -> int:
    if count == 0:
        return 0
    return min(4, max(1, math.ceil(4 * count / maximum)))


def render(snapshot: dict, config: dict, mobile: bool = False) -> str:
    days = validated_days(snapshot)
    p = config["palette"]
    colors = p["contributions"]
    if len(colors) != 5:
        raise ValueError("Exactly five contribution colors are required")
    # Real calendar coordinates: Sunday first, one column per week.
    first = days[0][0] - timedelta(days=(days[0][0].weekday() + 1) % 7)
    columns = ((days[-1][0] - first).days // 7) + 1
    width, pitch, cell = (320, 18, 13) if mobile else (960, 16, 11)
    x0, y0 = (34, 104) if mobile else ((width - columns * pitch + pitch - cell) / 2, 76)
    def coordinate(column, row):
        if mobile:
            return x0 + (column % 14) * pitch, y0 + (column // 14) * 156 + row * pitch
        return x0 + column * pitch, y0 + row * pitch
    if mobile:
        positions = []
        for block in range(math.ceil(columns / 14)):
            for row in range(7):
                available = list(range(block * 14, min(columns, (block + 1) * 14)))
                if (row + block) % 2:
                    available.reverse()
                positions.extend(coordinate(column, row) for column in available)
    else:
        positions = route_points(columns, x0, y0, pitch)
    height = 104 + math.ceil(columns / 14) * 156 + 50 if mobile else 226
    indices = {point: i for i, point in enumerate(positions)}
    duration = 56
    traversal_end = 92
    maximum = max((count for _, count in days), default=0)
    total = sum(count for _, count in days)
    title = "Contribution Activity"
    detail = f"{snapshot['start_date']} — {snapshot['end_date']} · public commits, opened PRs and issues"
    styles = [
        ".snake-segment{opacity:0;animation:travel 56s linear infinite}",
        ".eaten{animation-duration:56s;animation-timing-function:linear;animation-iteration-count:infinite}",
        "@media(prefers-reduced-motion:reduce){.snake-segment{display:none}.eaten{animation:none!important}}",
    ]
    frames = []
    for i, (x, y) in enumerate(positions):
        percent = 2 + traversal_end * i / max(1, len(positions) - 1)
        frames.append(f"{percent:.5f}%{{transform:translate({x:.2f}px,{y:.2f}px);opacity:1}}")
    sx, sy = positions[0]
    ex, ey = positions[-1]
    styles.append(f"@keyframes travel{{0%{{transform:translate({sx:.2f}px,{sy:.2f}px);opacity:0}}" + "".join(frames) + f"95%,100%{{transform:translate({ex:.2f}px,{ey:.2f}px);opacity:0}}}}")
    cells = []
    for day, count in days:
        delta = (day - first).days
        column, row = delta // 7, delta % 7
        x, y = coordinate(column, row)
        color = colors[level_for(count, maximum)]
        title_text = escape(f"{day.isoformat()}: {count} public activity events")
        animation = ""
        if count:
            at = 2 + traversal_end * indices[(x, y)] / max(1, len(positions) - 1)
            name = f"eat{delta}"
            styles.append(f"@keyframes {name}{{0%,{max(0,at-.01):.5f}%{{fill:{color}}}{at:.5f}%,96%{{fill:{colors[0]}}}99%,100%{{fill:{color}}}}}")
            animation = f' class="eaten" style="animation-name:{name}"'
        cells.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cell}" height="{cell}" rx="3" fill="{color}"{animation}><title>{title_text}</title></rect>')
    segments = []
    # Tail follows the head at the speed of one calendar cell per segment.
    lag = duration * .92 / max(1, len(positions) - 1)
    for i in range(5, -1, -1):
        opacity = 1 - i * .12
        segments.append(f'<g opacity="{opacity:.2f}"><rect class="snake-segment" width="{cell}" height="{cell}" rx="3.5" fill="{p["snake"]}" style="animation-delay:{i*lag:.5f}s"/></g>')
    months = []
    seen = set()
    previous_label_x = -100
    for day, _ in days:
        key = (day.year, day.month)
        column = (day - first).days // 7
        if key not in seen and (day.day <= 7 or not seen):
            seen.add(key)
            label_x = x0 + column*pitch
            if not mobile and label_x - previous_label_x >= 38:
                months.append(f'<text x="{label_x:.2f}" y="64" font-size="12" fill="{p["muted"]}">{day.strftime("%b")}</text>')
                previous_label_x = label_x
    if mobile:
        for block in range(math.ceil(columns / 14)):
            begin = max(days[0][0], first + timedelta(days=block * 98))
            end = min(days[-1][0], first + timedelta(days=(block + 1) * 98 - 1))
            label = f'{begin.strftime("%b %d")} — {end.strftime("%b %d")}'
            months.append(f'<text x="34" y="{86 + block * 156}" font-size="13" fill="{p["muted"]}">{label}</text>')
    date_line = f'<text x="{24 if mobile else 928}" y="{57 if mobile else 32}" text-anchor="{"start" if mobile else "end"}" fill="{p["muted"]}" font-size="12">{escape(snapshot["start_date"])} — {escape(snapshot["end_date"])}</text>'
    footer = (f'<text x="24" y="{height-54}" fill="{p["muted"]}" font-size="13">Public commits · opened PRs / issues</text><text x="24" y="{height-29}" fill="{p["muted"]}" font-size="13">{total} events · UTC · public data only</text>' if mobile else f'<text x="32" y="207" fill="{p["muted"]}" font-size="12">Public commits · opened pull requests · opened issues</text><text x="928" y="207" text-anchor="end" fill="{p["muted"]}" font-size="12">{total} events</text>')
    out = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="snake-title snake-desc">
<title id="snake-title">{title}</title>
<desc id="snake-desc">{escape(detail)}. {total} events. Gold snake traverses the calendar and temporarily clears colored cells. The original counts remain in the accessible cell titles. Animation respects reduced motion.</desc>
<style>{''.join(styles)}</style>
<rect x="1" y="1" width="{width-2}" height="{height-2}" rx="18" fill="{p['background']}" stroke="{p['border']}"/>
<g font-family="Arial,Helvetica,sans-serif">
<text x="{24 if mobile else 32}" y="32" fill="{p['text']}" font-size="15" font-weight="600">Public activity</text>
{date_line}
{''.join(months)}{''.join(cells)}{''.join(segments)}
{footer}
</g></svg>
'''
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--config", type=Path, default=Path("config/profile.json"))
    parser.add_argument("--output", type=Path, default=Path("assets/generated/contribution-snake.svg"))
    args = parser.parse_args()
    output = render(json.loads(args.snapshot.read_text(encoding="utf-8")), json.loads(args.config.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(output, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
