import copy
import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from scripts.generate_stats import render

def fixtures():
    config=json.loads((Path(__file__).parents[1]/'config/profile.json').read_text())
    snapshot={'scope':{'public_only':True},'kpis':{'commits':12,'pull_requests':3,'stars':4,'issues':2},'languages':{},'start_date':'2025-01-01','end_date':'2025-12-31'}
    return config,snapshot

def test_kpi_svg_reports_period_and_distinct_stock_definition():
    c,s=fixtures(); svg=render(s,c);root=ET.fromstring(svg)
    assert root.get('viewBox')=='0 0 560 520'
    assert '2025-01-01' in svg and 'Current total · lifetime' in svg
    assert svg==render(s,c)

@pytest.mark.parametrize('value',[None,True,-1,'0'])
def test_missing_kpi_does_not_render_zero(value):
    c,s=fixtures();s['kpis']['commits']=value
    with pytest.raises(ValueError):render(s,c)
