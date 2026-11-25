"""Generate self-contained technology cards from vendored brand assets.

No network is used. Source revision, colors and licenses live in
assets/icons/metadata.json. Unverified logos are deliberately rendered as text.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

SVG_NS = 'http://www.w3.org/2000/svg'
CATEGORY_FILES = {
    'Programming Languages': 'programming-languages.svg',
    'Data Science & AI': 'data-science-ai.svg',
    'Web & Database': 'web-database.svg',
    'Development Tools': 'development-tools.svg',
}


def _brand_markup(asset_dir: Path, metadata: dict) -> str:
    """Load verified path geometry without scripts or external dependencies."""
    file = metadata.get('file')
    if not file:
        return ''
    path = asset_dir / file
    if path.resolve().parent != asset_dir.resolve():
        raise ValueError('Icon file must be directly inside the local asset directory')
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != metadata['sha256']:
        raise ValueError(f'Vendored icon checksum mismatch: {file}')
    root = ET.fromstring(raw)
    if root.get('viewBox') != '0 0 24 24':
        raise ValueError(f'Unexpected brand icon aspect ratio: {file}')
    parts = []
    for node in root:
        tag = node.tag.rsplit('}', 1)[-1]
        if tag == 'title':
            continue
        if tag != 'path' or set(node.attrib) - {'d'}:
            raise ValueError(f'Unsupported SVG content: {file}')
        parts.append(f'<path d="{html.escape(node.attrib["d"], quote=True)}"/>')
    return ''.join(parts)


def _color(value: str) -> str:
    if not re.fullmatch(r'#[0-9A-Fa-f]{6}', value):
        raise ValueError('Expected a six-digit hexadecimal color')
    return value


def render_card(category: str, technologies: list[str], palette: dict, icons: dict,
                asset_dir: Path) -> str:
    """Render a 560px card with 24px labels for narrow-screen readability."""
    width = 560
    rows = max(4, (len(technologies) + 1) // 2)
    height = 106 + rows * 64 + 20
    p = {k: _color(palette[k]) for k in ('card', 'border', 'accent', 'text', 'muted')}
    escaped = html.escape(category)
    out = [
        f'<svg xmlns="{SVG_NS}" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escaped}</title>',
        f'<desc id="desc">{html.escape(", ".join(technologies))}. Listed technologies indicate experience, not proficiency ratings.</desc>',
        f'<rect x=".5" y=".5" width="559" height="{height - 1}" rx="18" fill="{p["card"]}" stroke="{p["border"]}"/>',
        f'<rect x="28" y="28" width="3" height="26" rx="1.5" fill="{p["accent"]}"/>',
        f'<text x="44" y="49" font-family="Inter,Arial,sans-serif" font-size="24" font-weight="600" fill="{p["text"]}">{escaped}</text>',
        f'<path d="M28 77H532" stroke="{p["border"]}"/>',
    ]
    for i, name in enumerate(technologies):
        if name not in icons:
            raise ValueError(f'No logo or documented text fallback for {name}')
        x = 28 + (i % 2) * 258
        y = 102 + (i // 2) * 64
        item = icons[name]
        brand = _brand_markup(asset_dir, item)
        out.append(f'<g aria-label="{html.escape(name, quote=True)}">')
        if brand:
            out.append(f'<rect x="{x}" y="{y}" width="44" height="44" rx="11" fill="#222222"/>')
            out.append(f'<g transform="translate({x + 8} {y + 8}) scale(1.1666667)" fill="{_color(item["display_color"])}">{brand}</g>')
            text_x = x + 58
        else:
            # Product name only: no invented symbol, monogram, or substitute brand.
            text_x = x
        if name == 'Visual Studio Code':
            out.append(f'<text x="{text_x}" y="{y + 18}" font-family="Inter,Arial,sans-serif" font-size="24" fill="{p["text"]}">Visual Studio<tspan x="{text_x}" dy="27">Code</tspan></text>')
        else:
            out.append(f'<text x="{text_x}" y="{y + 29}" font-family="Inter,Arial,sans-serif" font-size="24" fill="{p["text"]}">{html.escape(name)}</text>')
        out.append('</g>')
    out.append('</svg>\n')
    rendered = '\n'.join(out)
    ET.fromstring(rendered)
    return rendered


def generate(config_path: Path, output_dir: Path | None = None) -> list[Path]:
    config_path = Path(config_path).resolve()
    root = config_path.parent.parent
    config = json.loads(config_path.read_text(encoding='utf-8'))
    asset_dir = root / 'assets' / 'icons'
    metadata = json.loads((asset_dir / 'metadata.json').read_text(encoding='utf-8'))
    output_dir = Path(output_dir) if output_dir else root / 'assets' / 'tech'
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for category, names in config['tech_stack'].items():
        if category not in CATEGORY_FILES:
            raise ValueError(f'Unknown category: {category}')
        path = output_dir / CATEGORY_FILES[category]
        path.write_text(render_card(category, names, config['palette'], metadata['icons'], asset_dir), encoding='utf-8', newline='\n')
        paths.append(path)
    return paths


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=Path(__file__).resolve().parents[1] / 'config/profile.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    for path in generate(args.config, args.output):
        print(path)


if __name__ == '__main__':
    main()
