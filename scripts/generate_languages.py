"""Language byte distribution, never a skill or proficiency score."""
from decimal import Decimal, ROUND_FLOOR
import math
try:
    from .svg_utils import start, text, validate_numbers
except ImportError:
    from svg_utils import start, text, validate_numbers

def distribution(languages, top=5):
    if type(top) is not int or not 1 <= top <= 5:
        raise ValueError('top_languages must be 1–5')
    if any(type(v) is not int or v < 0 for v in languages.values()):
        raise ValueError('Language sizes must be non-negative integers')
    ranked = sorted(((str(k), v) for k, v in languages.items() if v), key=lambda item: (-item[1], item[0]))
    total = sum(v for _, v in ranked)
    if not total:
        return []
    entries = ranked[:top]
    if len(ranked) > top:
        entries.append(('Other', sum(v for _, v in ranked[top:])))
    exact = [Decimal(v) * 1000 / total for _, v in entries]
    units = [int(v.to_integral_value(rounding=ROUND_FLOOR)) for v in exact]
    for i in sorted(range(len(entries)), key=lambda i: (-(exact[i]-units[i]), i))[:1000-sum(units)]:
        units[i] += 1
    return [{'name': name, 'bytes': size, 'fraction': size/total, 'percentage': units[i]/10} for i, (name, size) in enumerate(entries)]

def render(snapshot, config):
    validate_numbers(snapshot)
    p = config['palette']
    data = distribution(snapshot['languages'], config['analytics'].get('top_languages', 5))
    s = [start(560, 520, 'Language distribution', 'Based on public repository code size, not proficiency. Forks, archived repositories and this profile repository are excluded.', p['background']), text(28, 42, 'LANGUAGE DISTRIBUTION', 18, p['muted'], 600), text(28, 72, 'Based on public repository code size.', 16, p['muted'])]
    s.append(f'<rect x="24" y="100" width="512" height="350" rx="16" fill="{p["card"]}" stroke="{p["border"]}"/>')
    cx, cy, radius, circumference = 159, 248, 86, 2*math.pi*86
    s.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="#303030" stroke-width="22"/>')
    offset = 0
    for i, row in enumerate(data):
        length = row['fraction'] * circumference
        color = p['languages'][i]
        s.append(f'<circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" stroke-width="22" stroke-dasharray="{length:.6f} {circumference-length:.6f}" stroke-dashoffset="{-offset:.6f}" transform="rotate(-90 {cx} {cy})"/>')
        offset += length
        y = 164 + i * 44
        s.append(f'<rect x="282" y="{y-13}" width="10" height="10" rx="2" fill="{color}"/>')
        name = row['name'] if len(row['name']) <= 17 else row['name'][:16] + '…'
        s += [text(304, y, name, 17, p['text']), text(510, y, f"{row['percentage']:.1f}%", 17, p['text'], anchor='end')]
    if data:
        s += [text(cx, cy-2, str(len(snapshot['languages'])), 44, p['text'], 500, 'middle'), text(cx, cy+27, 'languages', 16, p['muted'], anchor='middle')]
    else:
        s += [text(cx, cy, 'No code', 22, p['text'], anchor='middle'), text(282, 235, 'No language bytes', 18, p['muted']), text(282, 262, 'in the selected scope.', 16, p['muted'])]
    s += [text(48, 416, f"{len(snapshot['repositories'])} included public repositories", 16, p['muted']), text(28, 484, f"Snapshot: {snapshot['as_of']} UTC · Not proficiency.", 16, p['muted']), '</svg>']
    return ''.join(s)

def render_mobile(snapshot, config):
    validate_numbers(snapshot)
    p=config['palette']; data=distribution(snapshot['languages'],config['analytics'].get('top_languages',5))
    height=440 if len(data)<=3 else 535
    s=[start(320,height,'Language distribution','Real public repository code size; not proficiency.',p['background']),text(16,32,'LANGUAGE DISTRIBUTION',15,p['muted'],600),text(16,58,'Public repository code size.',13,p['muted'])]
    s.append(f'<rect x="12" y="80" width="296" height="{height-126}" rx="12" fill="{p["card"]}" stroke="{p["border"]}"/>')
    radius=68;circ=2*math.pi*radius;offset=0
    s.append(f'<circle cx="160" cy="178" r="{radius}" fill="none" stroke="#303030" stroke-width="19"/>')
    for i,row in enumerate(data):
        length=row['fraction']*circ;color=p['languages'][i]
        s.append(f'<circle cx="160" cy="178" r="{radius}" fill="none" stroke="{color}" stroke-width="19" stroke-dasharray="{length:.6f} {circ-length:.6f}" stroke-dashoffset="{-offset:.6f}" transform="rotate(-90 160 178)"/>');offset+=length
        y=285+i*31
        s.append(f'<rect x="30" y="{y-11}" width="10" height="10" rx="2" fill="{color}"/>')
        s.extend([text(52,y,row['name'][:20],16,p['text']),text(288,y,f"{row['percentage']:.1f}%",16,p['text'],anchor='end')])
    s.extend([text(160,180,str(len(data)) if data else 'No code',34 if data else 20,p['text'],500,'middle'),text(160,205,'languages' if data else 'in selected scope',13,p['muted'],anchor='middle'),text(16,height-20,f"{snapshot['as_of']} UTC · Not proficiency",13,p['muted']),'</svg>'])
    return ''.join(s)
