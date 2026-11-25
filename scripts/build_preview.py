"""Create offline HTML views from the actual README (no publishing)."""
from pathlib import Path
from markdown_it import MarkdownIt

ROOT=Path(__file__).resolve().parents[1]

def build():
    target=ROOT/'previews';target.mkdir(exist_ok=True)
    raw=(ROOT/'README.md').read_text(encoding='utf-8')
    markup=MarkdownIt('commonmark',{'html':True}).render(raw)
    markup=markup.replace('src="./','src="../').replace('srcset="./','srcset="../')
    css='''*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;font-size:16px;line-height:1.6}body.dark{--bg:#0d1117;--fg:#e6edf3;--line:#30363d;--muted:#9da7b3;--link:#58a6ff}body.light{--bg:#fff;--fg:#1f2328;--line:#d1d9e0;--muted:#59636e;--link:#0969da}main{width:100%;max-width:930px;margin:32px auto;padding:32px;border:1px solid var(--line);border-radius:8px}header{font:12px Consolas,monospace;color:var(--muted);margin-bottom:24px}h2{font-size:21px;font-weight:600;letter-spacing:1.5px;border-bottom:1px solid var(--line);padding-bottom:14px;margin:42px 0 24px}h3{font-size:18px;font-weight:600;margin:26px 0 4px}p{margin:16px 0}img{max-width:100%;height:auto;vertical-align:top}picture{display:inline}p>img,p>a>img,p>picture>img{margin:0 3px 10px 0}a{color:var(--link);text-decoration:none}details{font-size:13px;color:var(--muted);margin:12px 0}summary{cursor:pointer}ul{padding-left:24px}li{margin:5px 0}em{color:var(--muted)}@media(max-width:600px){main{margin:0;border:0;border-radius:0;padding:16px}body{font-size:15px}h2{font-size:18px;margin-top:34px}p>img,p>a>img,p>picture>img{margin:0 0 10px}header{margin-bottom:18px}}'''
    for theme in ('dark','light'):
        html=f'<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Obsidian Emerald — {theme} preview</title><style>{css}</style><body class="{theme}"><main><header>a5my0u / README.md</header>{markup}</main></body></html>'
        (target/f'profile-{theme}.html').write_text(html,encoding='utf-8')
    (target/'header.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dark Silk header</title><style>body{margin:0;background:#0D0D0D}img{width:100%;height:auto;display:block}</style><picture><source media="(max-width:600px)" srcset="../assets/header/header-mobile.svg"><img src="../assets/header/header.svg" alt="Dark Silk header"></picture></html>',encoding='utf-8')
    print('Dark/light profile previews and a standalone header preview created.')

if __name__=='__main__':build()
