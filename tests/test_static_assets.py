import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from scripts.generate_header import render as header
from scripts.generate_readme import render as readme
from scripts.generate_tech_stack import generate

ROOT=Path(__file__).parents[1]

def config():return json.loads((ROOT/'config/profile.json').read_text(encoding='utf-8'))

def test_header_text_stays_still_and_motion_is_restricted():
    value=header(b'fixture JPEG',config())
    root=ET.fromstring(value)
    ns={'s':'http://www.w3.org/2000/svg'}
    assert root.find('.//s:animateTransform',ns).get('dur')=='16s'
    assert all(not node.findall('.//s:animateTransform',ns) for node in root.findall('.//s:text',ns))
    assert 'prefers-reduced-motion' in value
    assert 'animateTransform' not in header(b'fixture',config(),animated=False)

def test_mobile_header_and_static_fallback_exist():
    root=ET.fromstring(header(b'fixture',config(),mobile=True))
    assert root.get('viewBox')=='0 0 600 360'
    value=readme(config())
    assert 'header-mobile-static.svg' in value and '<summary>Static header' in value
    assert '<script' not in value and '<iframe' not in value

def test_unconfirmed_experience_and_achievement_not_published():
    c=config()
    c['experience'].append({'role':'Fixture Pending Role', 'start':'2020-01', 'end':None, 'publish':True, 'confirmation_required':True, 'details':['Synthetic test entry']})
    c['achievement']={'publish':True,'confirmation_required':True,'text':'Sensitive unconfirmed claim'}
    value=readme(c)
    assert 'Fixture Pending Role' not in value
    assert 'Sensitive unconfirmed claim' not in value

def test_private_projects_rejected():
    c=config();c['featured_projects']=[{'visibility':'private'}]
    with pytest.raises(ValueError):readme(c)

def test_tech_assets_regenerate_identically(tmp_path):
    paths=generate(ROOT/'config/profile.json',tmp_path)
    assert len(paths)==4
    for path in paths:
        ET.parse(path)
        assert path.read_bytes()==(ROOT/'assets/tech'/path.name).read_bytes()

def test_all_published_svg_xml_and_image_paths():
    for path in (ROOT/'assets').rglob('*.svg'):
        ET.parse(path)
    import re
    value=(ROOT/'README.md').read_text(encoding='utf-8')
    for path in re.findall(r'(?:src|srcset)="(\./[^"]+)"',value):
        assert (ROOT/path).exists(),path
