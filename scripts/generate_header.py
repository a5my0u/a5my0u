"""Build Dark Silk SVGs with fixed typography and a 16-second light sweep.

The JPEG texture is an original AI-generated project asset. It is embedded in
the SVG; there are no external image/font requests. Pillow is used only when
preparing a replacement texture or exporting the optional PNG preview.
"""
from __future__ import annotations
import argparse
import base64
from html import escape
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def render(texture: bytes, config: dict, animated=True, mobile=False):
    p, h = config['palette'], config['header']
    width, height = (600, 360) if mobile else (h['width'], h['height'])
    encoded = base64.b64encode(texture).decode('ascii')
    x = 36 if mobile else 60
    title_y, title_size = (146, 68) if mobile else (162, 78)
    field_y, field_size = (61, 26) if mobile else (68, 22)
    interest_y, interest_size = (205, 26) if mobile else (218, 26)
    location_y, location_size = (290, 26) if mobile else (274, 20)
    motion = ''
    if animated:
        motion = f'''<g class="reflection" clip-path="url(#right)"><ellipse cx="{width*.78:.0f}" cy="{height*.55:.0f}" rx="{width*.23:.0f}" ry="{height*.95:.0f}" fill="url(#light)" opacity=".12"><animateTransform attributeName="transform" type="translate" values="-80 0;65 -9;-80 0" dur="{h['loop_seconds']}s" repeatCount="indefinite"/><animate attributeName="opacity" values=".05;.12;.05" dur="{h['loop_seconds']}s" repeatCount="indefinite"/></ellipse></g>'''
    value = f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="header-title header-desc">
<title id="header-title">{escape(config['username'])} — Data Science / Engineering</title>
<desc id="header-desc">Machine Learning, AI and Software. Chiba University, Japan. Black silk with a subtle emerald reflection; the text remains still.</desc>
<defs>
<clipPath id="frame"><rect width="{width}" height="{height}" rx="18"/></clipPath>
<clipPath id="right"><rect x="{width*.45:.0f}" width="{width*.55:.0f}" height="{height}"/></clipPath>
<linearGradient id="shade"><stop stop-color="#0D0D0D" stop-opacity=".42"/><stop offset=".56" stop-color="#0D0D0D" stop-opacity=".12"/><stop offset="1" stop-color="#0D0D0D" stop-opacity="0"/></linearGradient>
<radialGradient id="light"><stop stop-color="#C8F7E5" stop-opacity=".34"/><stop offset=".4" stop-color="#34D399" stop-opacity=".15"/><stop offset="1" stop-color="#34D399" stop-opacity="0"/></radialGradient>
</defs>
<style>@media(prefers-reduced-motion:reduce){{.reflection{{display:none}}}}</style>
<g clip-path="url(#frame)">
<rect width="{width}" height="{height}" fill="{p['background']}"/>
<image width="{width}" height="{height}" preserveAspectRatio="xMidYMid slice" xlink:href="data:image/jpeg;base64,{encoded}"/>
<rect width="{width}" height="{height}" fill="url(#shade)"/>
{motion}
<g font-family="'Segoe UI',Arial,Helvetica,sans-serif">
<text x="{x}" y="{field_y}" fill="{p['accent']}" font-size="{field_size}" font-weight="500" letter-spacing="2.1">{escape(h['field'])}</text>
<text x="{x-3}" y="{title_y}" fill="{p['text']}" font-size="{title_size}" font-weight="600" letter-spacing="-2">{escape(config['username'])}</text>
<text x="{x}" y="{interest_y}" fill="#D4D4D8" font-size="{interest_size}" font-weight="400">{escape(h['interests'])}</text>
<path d="M{x} {location_y-9}h22" stroke="{p['accent']}" stroke-width="2"/>
<text x="{x+36}" y="{location_y}" fill="{p['muted']}" font-size="{location_size}" letter-spacing="1.4">{escape(h['location'])}</text>
</g></g>
<rect x=".5" y=".5" width="{width-1}" height="{height-1}" rx="18" fill="none" stroke="{p['border']}"/>
</svg>'''
    ET.fromstring(value)
    return value

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config', type=Path, default=ROOT/'config/profile.json')
    parser.add_argument('--texture', type=Path, help='Optional new original texture to optimize locally')
    args = parser.parse_args()
    config = json.loads(args.config.read_text(encoding='utf-8'))
    folder = args.config.resolve().parent.parent/'assets/header'
    folder.mkdir(parents=True, exist_ok=True)
    if args.texture:
        from PIL import Image
        with Image.open(args.texture) as image:
            image.convert('RGB').resize((1800, 600), Image.Resampling.LANCZOS).save(folder/'silk-texture.jpg', quality=86, optimize=True)
    texture = (folder/'silk-texture.jpg').read_bytes()
    for name, animated, mobile in [('header.svg', True, False), ('header-static.svg', False, False), ('header-mobile.svg', True, True), ('header-mobile-static.svg', False, True)]:
        (folder/name).write_text(render(texture, config, animated, mobile), encoding='utf-8')
    print('Dark Silk desktop/mobile and animated/static SVGs generated.')

if __name__ == '__main__':
    main()
