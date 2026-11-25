"""Render an original 2x2 KPI panel from verified public data."""
try:
    from .svg_utils import start, text, validate_numbers
except ImportError:
    from svg_utils import start, text, validate_numbers

def render(snapshot, config):
    validate_numbers(snapshot)
    p = config['palette']
    s = [start(560, 520, 'GitHub analytics — public activity', 'Commits, pull requests and issues use the stated UTC window. Stars are a current snapshot.', p['background'])]
    s += [text(28, 42, 'PUBLIC ACTIVITY', 18, p['muted'], 600), text(28, 72, f"{snapshot['start_date']} — {snapshot['end_date']} UTC", 16, p['muted'])]
    cards = [('commits', 'Commits', 'Default-branch commits', 24, 100), ('pull_requests', 'Pull Requests', 'Opened in public repos', 292, 100), ('stars', 'Stars', 'Current total · lifetime', 24, 284), ('issues', 'Issues', 'Opened in public repos', 292, 284)]
    for key, label, note, x, y in cards:
        s.append(f'<rect x="{x}" y="{y}" width="244" height="166" rx="16" fill="{p["card"]}" stroke="{p["border"]}"/>')
        s.append(f'<rect x="{x+20}" y="{y+22}" width="3" height="18" rx="1.5" fill="{p["accent"]}"/>')
        s += [text(x+34, y+37, label, 20, p['muted']), text(x+20, y+106, f"{snapshot['kpis'][key]:,}", 53 if snapshot['kpis'][key] < 1000000 else 39, p['text'], 500), text(x+20, y+140, note, 16, p['muted'])]
    s += [text(28, 484, 'Public data only. Profile repository excluded.', 16, p['muted']), '</svg>']
    return ''.join(s)

def render_mobile(snapshot, config):
    validate_numbers(snapshot)
    p = config['palette']
    s = [start(320, 430, 'Public GitHub activity', 'Same real data as the desktop KPI panel. Stars are a current lifetime total.', p['background']), text(16, 32, 'PUBLIC ACTIVITY', 15, p['muted'], 600), text(16, 58, f"{snapshot['start_date']} — {snapshot['end_date']}", 13, p['muted'])]
    for key, label, note, x, y in [('commits','Commits',['Default branch','commits'],12,80),('pull_requests','Pull Requests',['Public PRs','opened'],166,80),('stars','Stars',['Current total','Lifetime stock'],12,249),('issues','Issues',['Public issues','opened'],166,249)]:
        s.append(f'<rect x="{x}" y="{y}" width="142" height="157" rx="12" fill="{p["card"]}" stroke="{p["border"]}"/>')
        s += [text(x+14,y+29,label,15,p['muted']),text(x+14,y+91,f"{snapshot['kpis'][key]:,}",43 if snapshot['kpis'][key]<10000 else 28,p['text'],500),text(x+14,y+120,note[0],13,p['muted']),text(x+14,y+139,note[1],13,p['muted'])]
    return ''.join(s)+'</svg>'
