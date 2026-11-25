"""Small deterministic SVG primitives shared by static dashboard renderers."""
from html import escape

def text(x, y, content, size=18, color='#F5F5F5', weight=400, anchor='start'):
    return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" font-family="Arial,Helvetica,sans-serif">{escape(str(content))}</text>'

def start(width, height, title, description, background='#0D0D0D'):
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc"><title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc><rect width="{width}" height="{height}" rx="18" fill="{background}"/>'

def validate_numbers(snapshot):
    if snapshot.get('scope', {}).get('public_only') is not True:
        raise ValueError('Only public snapshots may be rendered')
    for key in ('commits', 'pull_requests', 'stars', 'issues'):
        if type(snapshot.get('kpis', {}).get(key)) is not int or snapshot['kpis'][key] < 0:
            raise ValueError('Missing or invalid KPI: ' + key)
    if not isinstance(snapshot.get('languages'), dict):
        raise ValueError('Missing language data')
    for size in snapshot['languages'].values():
        if type(size) is not int or size < 0:
            raise ValueError('Invalid language byte count')
