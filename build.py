#!/usr/bin/env python3
"""Build the SAYU site: site/src/pages/*.html → site/public/*.html.

Each page starts with a JSON header in an HTML comment:
    <!--{"title": "...", "description": "...", "nav": "download"}-->
The layout adds <head>, the navigation and the footer. `{{icon:name}}` inserts
an inline SVG icon (one stroke family, drawn for this site). Deploy site/public.
"""
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
SRC = ROOT / 'src/pages'
OUT = ROOT / 'public'
EMAIL = 'jonyeock@gmail.com'
SITE_URL = 'https://donkey-haw.github.io/SAYU-app/'

ICONS = {
    'download': '<path d="M10 3.5v9M6 9l4 4 4-4M4 16.5h12"/>',
    'chevron': '<path d="M7.5 4.5 13 10l-5.5 5.5"/>',
    'mac': '<rect x="2.5" y="3.5" width="15" height="10" rx="1.6"/><path d="M7 16.5h6M10 13.5v3"/>',
    'nostudent': '<circle cx="10" cy="7" r="3"/><path d="M4 17c1.2-3.2 3.4-4.8 6-4.8s4.8 1.6 6 4.8"/><path d="M3 3l14 14"/>',
    'shield': '<path d="M10 2.8 16 5v4.6c0 3.6-2.5 6.3-6 7.6-3.5-1.3-6-4-6-7.6V5z"/><path d="m7.4 10 1.8 1.8 3.6-3.6"/>',
    'key': '<circle cx="7" cy="12.5" r="3.5"/><path d="M9.5 10 16 3.5M13.5 6l2 2"/>',
    'mail': '<rect x="2.5" y="4.5" width="15" height="11" rx="1.6"/><path d="m3 5.5 7 5.5 7-5.5"/>',
    'chat': '<path d="M3.5 5.5a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2H9l-3.5 3v-3h0a2 2 0 0 1-2-2z"/>',
    'undo': '<path d="M5 8h7a4 4 0 0 1 0 8H8"/><path d="M8 5 5 8l3 3"/>',
    'sparkle': '<path d="M10 2.5c.6 3.7 2.8 5.9 6.5 6.5-3.7.6-5.9 2.8-6.5 6.5-.6-3.7-2.8-5.9-6.5-6.5 3.7-.6 5.9-2.8 6.5-6.5z"/>',
    'doc': '<path d="M5.5 2.5h6l3.5 3.5v11a.9.9 0 0 1-.9.9H5.5a.9.9 0 0 1-.9-.9V3.4a.9.9 0 0 1 .9-.9z"/><path d="M11.5 2.5V6h3.5M7.5 10h5M7.5 13h5"/>',
    'sidebar': '<rect x="2.5" y="3.5" width="15" height="13" rx="1.6"/><path d="M7.5 3.5v13"/>',
    'gear': '<circle cx="10" cy="10" r="2.6"/><path d="M10 2.5v2M10 15.5v2M2.5 10h2M15.5 10h2M4.7 4.7l1.4 1.4M13.9 13.9l1.4 1.4M4.7 15.3l1.4-1.4M13.9 6.1l1.4-1.4"/>',
    'paperclip': '<path d="M14.5 9.5 9 15a3.5 3.5 0 0 1-5-5l6-6a2.3 2.3 0 0 1 3.3 3.3l-6 6a1.1 1.1 0 0 1-1.6-1.6L11 6.5"/>',
    'up': '<path d="M10 16V4M5.5 8.5 10 4l4.5 4.5"/>',
    'folder': '<path d="M2.5 5.5A1.5 1.5 0 0 1 4 4h4.2l1.8 2H16a1.5 1.5 0 0 1 1.5 1.5V15a1.5 1.5 0 0 1-1.5 1.5H4A1.5 1.5 0 0 1 2.5 15z"/><path d="M2.5 8.5h15"/>',
    'bulb': '<path d="M7.2 13.2c0-1.4-2.2-2.6-2.2-5.4a5 5 0 0 1 10 0c0 2.8-2.2 4-2.2 5.4"/><path d="M7.6 15.5h4.8M8.4 17.8h3.2"/>',
    'board': '<rect x="2.5" y="3.5" width="15" height="13" rx="1.6"/><path d="M2.5 7h15M6.25 7v9.5M10 7v9.5M13.75 7v9.5"/>',
    'sliders': '<path d="M3.5 6h7M14.5 6h2M3.5 14h2M9.5 14h7"/><circle cx="12.5" cy="6" r="2"/><circle cx="7.5" cy="14" r="2"/>',
    'check': '<circle cx="10" cy="10" r="7.5"/><path d="m6.8 10.2 2.2 2.2 4.2-4.4"/>',
    'arrow': '<path d="M4 10h12M11.5 5.5 16 10l-4.5 4.5"/>',
    'book': '<path d="M10 5.5c-1.6-1.3-3.8-2-6.5-2v11c2.7 0 4.9.7 6.5 2 1.6-1.3 3.8-2 6.5-2v-11c-2.7 0-4.9.7-6.5 2z"/><path d="M10 5.5v11"/>',
}


def icon(name, size=20, cls='icon'):
    return (f'<svg class="{cls}" width="{size}" height="{size}" viewBox="0 0 20 20" fill="none" stroke="currentColor" '
            f'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


# Section links of the intro page, then the reading pages.
SECTIONS = [('features', '주요 기능'), ('flow', '이용 과정'), ('examples', '활용 예시'), ('faq', '자주 묻는 질문')]
PAGES = [('guide', 'guide.html', '도움말'), ('pilot', 'pilot.html', '파일럿')]

LAYOUT = '''<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{description}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{site}assets/img/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="canonical" href="{url}">
<meta name="theme-color" content="#ffffff">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="icon" href="favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css">
<link rel="stylesheet" href="assets/site.css?v={css_v}">
<script src="assets/site.js?v={js_v}" defer></script>
</head>
<body class="page-{nav}">
<a class="skip" href="#main">본문으로 건너뛰기</a>
<header class="nav" id="nav">
  <div class="nav-in">
    <a class="brand" href="./" aria-label="SAYU 처음으로"><img src="assets/img/sayu-mark.svg" alt="" width="26" height="22">SAYU</a>
    <nav class="nav-links" aria-label="소개 페이지 구역">{sections}</nav>
    <nav class="nav-pages" aria-label="사이트">{pages}</nav>
    <a class="btn btn-small" href="download.html">{download}무료로 내려받기</a>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <div class="foot-in">
    <div class="foot-brand"><a class="brand" href="./"><img src="assets/img/sayu-mark.svg" alt="" width="22" height="19">SAYU</a>
      <p>선생님의 생각과 AI가 만나 그리는 수업. 교사 파일럿 체험판.</p></div>
    <nav class="foot-cols" aria-label="바닥글">
      <div><h2>SAYU</h2><a href="./">소개</a><a href="download.html">내려받기</a><a href="changelog.html">업데이트 기록</a></div>
      <div><h2>도움</h2><a href="guide.html">도움말</a><a href="pilot.html">파일럿 참여</a><a href="mailto:{email}">문의하기</a></div>
      <div><h2>정책</h2><a href="privacy.html">개인정보 안내</a><a href="terms.html">체험판 이용 조건</a></div>
    </nav>
  </div>
  <div class="foot-legal">
    <span>© 2026 SAYU</span>
    <span>Apple, Mac, Numbers는 Apple Inc.의 상표입니다. ChatGPT는 OpenAI, Claude는 Anthropic의 상표입니다. SAYU는 이들 회사와 관련이 없습니다.</span>
  </div>
</footer>
</body>
</html>
'''


def version(path):
    # Content hash in the URL so browsers fetch a changed file at once
    # (GitHub Pages lets them cache assets for 10 minutes).
    return hashlib.sha256((OUT / path).read_bytes()).hexdigest()[:10]


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    css_v, js_v = version('assets/site.css'), version('assets/site.js')
    for page in sorted(SRC.glob('*.html')):
        text = page.read_text()
        header = re.match(r'<!--(\{.*?\})-->\n', text, re.S)
        meta = json.loads(header.group(1))
        body = text[header.end():]
        body = re.sub(r'\{\{icon:(\w+)(?::(\d+))?\}\}', lambda m: icon(m.group(1), int(m.group(2) or 20)), body)
        body = body.replace('{{email}}', EMAIL)
        here = meta.get('nav')
        prefix = '' if page.stem == 'index' else './'
        sections = ''.join(f'<a href="{prefix}#{key}">{label}</a>' for key, label in SECTIONS)
        pages = ''.join(f'<a href="{href}"{" aria-current=\"page\"" if key == here else ""}>{label}</a>' for key, href, label in PAGES)
        url = SITE_URL + ('' if page.stem == 'index' else page.name)
        html = LAYOUT.format(css_v=css_v, js_v=js_v, site=SITE_URL, url=url, title=meta['title'], description=meta['description'], nav=meta.get('nav', page.stem), sections=sections, pages=pages, download=icon('download', 16), body=body, email=EMAIL)
        (OUT / page.name).write_text(html)
        print('built', page.name)


if __name__ == '__main__':
    build()
