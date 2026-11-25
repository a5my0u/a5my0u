import json
from pathlib import Path
import xml.etree.ElementTree as ET
import pytest
from scripts.generate_languages import distribution,render

def test_percentages_sum_to_100_and_other_uses_real_bytes():
    result=distribution({'A':1,'B':1,'C':1,'D':1,'E':1,'F':1,'G':1},5)
    assert sum(round(row['percentage']*10) for row in result)==1000
    assert result[-1]['name']=='Other' and result[-1]['bytes']==2
    assert result==distribution({'G':1,'E':1,'D':1,'C':1,'A':1,'B':1,'F':1},5)

def test_zero_and_one_language_are_not_division_errors():
    assert distribution({})==[]
    assert distribution({'Python':0})==[]
    assert distribution({'Python':12})[0]['percentage']==100

@pytest.mark.parametrize('bad',[None,-1,True,3.4])
def test_invalid_bytes_rejected(bad):
    with pytest.raises(ValueError):distribution({'Python':bad})

def test_labels_escaped_and_svg_is_valid():
    c=json.loads((Path(__file__).parents[1]/'config/profile.json').read_text())
    s={'scope':{'public_only':True},'kpis':dict.fromkeys(['commits','pull_requests','stars','issues'],0),'languages':{'<script>':15},'repositories':[],'as_of':'2026-01-01'}
    result=render(s,c)
    assert '&lt;script&gt;' in result and '<script>' not in result
    ET.fromstring(result)
