"""Render the existing lab Markdown and package a deterministic teaching download.

Authored homepage stays at repository root. The reviewed lab manifest determines
the ZIP contents; earlier teaching releases are preserved in downloads/archive.
"""
from pathlib import Path
import hashlib
import html
import json
import re
import shutil
import zipfile
import markdown

ROOT = Path(__file__).resolve().parents[1]
LAB = ROOT / 'gc1991-lab'
GUIDES = ROOT / 'guides/gc1991'
REPO = 'https://github.com/mengyulin/2026_Hydraulic-Jump_Project'
PAGES = {
    'install-windows': ('Windows／WSL 安裝', 'docs/install-windows.md'),
    'install-macos': ('macOS 安裝', 'docs/install-macos.md'),
    'quickstart': ('操作指南與作業', 'docs/quickstart.md'),
    'methods': ('方程與方法', 'docs/methods.md'),
    'code-guide': ('程式導讀', 'docs/code-guide.md'),
    'troubleshooting': ('疑難排解', 'docs/troubleshooting.md'),
    'verification': ('本機驗證紀錄', 'docs/verification.md'),
    'instructor': ('教師維護', 'docs/instructor.md'),
    'credits': ('資料來源與授權', 'THIRD_PARTY_NOTICES.md'),
}
SOURCE_TO_PAGE = {(LAB / path).resolve(): slug for slug, (_, path) in PAGES.items()}


def render_markdown(source):
    text = source.read_text()
    # Protect TeX before Markdown handles underscores, escapes and table pipes.
    # Leave fenced/inline code verbatim: dollar signs there are ordinary code.
    equations = []
    def protect(match, display):
        token = f'EQUATIONPLACEHOLDER{len(equations)}END'
        equations.append((token, match.group(1), display))
        return f'\n\n{token}\n\n' if display else token
    parts = re.split(r'(```[^\n]*\n.*?^```[ \t]*$|~~~[^\n]*\n.*?^~~~[ \t]*$|`+[^`\n]*`+)', text, flags=re.S | re.M)
    for i in range(0, len(parts), 2):
        parts[i] = re.sub(r'\$\$(.*?)\$\$', lambda m: protect(m, True), parts[i], flags=re.S)
        parts[i] = re.sub(r'(?<![\\$])\$(?!\$)([^\n$]+?)\$(?!\$)', lambda m: protect(m, False), parts[i])
    text = ''.join(parts)
    rendered = markdown.markdown(text, extensions=['tables', 'fenced_code', 'toc'])
    for token, equation, display in equations:
        if display:
            rendered = rendered.replace(f'<p>{token}</p>',
                f'<div class="math-display" tabindex="0" role="region" aria-label="公式，可左右捲動">\\[{html.escape(equation)}\\]</div>')
        else:
            rendered = rendered.replace(token, f'<span class="math-inline">\\({html.escape(equation)}\\)</span>')
    rendered = re.sub(r'(<h2[^>]*>本章導覽</h2>\s*<ul>.*?</ul>)',
                      r'<nav class="chapter-toc" aria-label="本章導覽">\1</nav>', rendered, flags=re.S)
    def rewrite(match):
        attr, link = match.group(1), html.unescape(match.group(2))
        if re.match(r'^(?:[a-z]+:|#|//)', link, re.I):
            return match.group(0)
        path, separator, fragment = link.partition('#')
        target = (source.parent / path).resolve()
        if target in SOURCE_TO_PAGE:
            url = SOURCE_TO_PAGE[target] + '.html'
        elif target == LAB / 'README.md':
            url = '../../gc1991-lab/index.html'
        elif attr == 'href' and target.suffix in {'.py', '.c', '.h', '.patch', '.ipynb'}:
            url = REPO + '/blob/main/' + target.relative_to(ROOT).as_posix()
        else:
            url = '../../' + target.relative_to(ROOT).as_posix()
        if separator:
            url += '#' + fragment
        return f'{attr}="{html.escape(url, quote=True)}"'
    rendered = re.sub(r'(href|src)="([^"]+)"', rewrite, rendered)
    return rendered.replace('<table>', '<div class="table-wrap" tabindex="0" role="region" aria-label="文件表格，可左右捲動"><table>').replace('</table>', '</table></div>')


def guide_page(slug, title, source):
    style_version = hashlib.sha256((ROOT / 'assets/site.css').read_bytes()).hexdigest()[:12]
    nav = ''.join(f'<a href="{key}.html"' + (' aria-current="page"' if key == slug else '') + f'>{name}</a>' for key, (name, _) in PAGES.items())
    if slug == 'methods':
        nav += '<a href="#main">本章導覽 ↑</a>'
    legacy = ''
    if slug in {'instructor', 'credits'}:
        legacy = '<div class="notice">以下保留 v1 教材的原始發行紀錄；其中「尚未發布」描述當時狀態。目前網站入口位於主專題首頁，網站維護方式見 <a href="' + REPO + '/blob/main/docs/website-maintenance.md">網站維護說明</a>。原始材料的授權聲明維持不變。</div>'
    math = ''
    if slug == 'methods':
        config = {'tex': {'inlineMath': [['\\(', '\\)']]}, 'svg': {'fontCache': 'local'}, 'options': {'enableMenu': False}}
        math = '<script>window.MathJax=' + json.dumps(config) + ';</script><script defer src="../../assets/vendor/mathjax/tex-svg.js"></script>'
    return f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>{title}｜GC1991 水躍實驗室</title><meta name="description" content="GC1991 水躍教學教材：{title}。"><link rel="icon" href="../../assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="../../assets/site.css?v={style_version}"><script defer src="../../assets/site.js"></script>{math}</head><body>
<a class="skip" href="#main">跳到主要內容</a><header class="site-header"><div class="wrap header-inner"><a class="brand" href="../../index.html"><span class="mark" aria-hidden="true">HJ</span><span><strong>水躍學生專題</strong><small>HYDRAULIC JUMP PROJECT</small></span></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav">選單</button><nav class="nav" id="site-nav" aria-label="主要導覽"><a href="../../index.html#projects">全部工作項目</a><a href="../../gc1991-lab/index.html">GC1991 實驗室</a><a href="quickstart.html">操作指南</a><a href="{REPO}">GitHub ↗</a></nav></div></header>
<div class="wrap"><p class="breadcrumb"><a href="../../index.html">專題首頁</a> / <a href="../../gc1991-lab/index.html">GC1991 實驗室</a> / {title}</p></div><div class="wrap doc-layout"><nav class="doc-nav" aria-label="教材文件"><h2>GC1991 教材文件</h2>{nav}<a href="../../downloads/gc1991-lab-v1.zip" download>下載完整教材 ↓</a></nav><main id="main" class="doc-content">{legacy}{render_markdown(source)}<p class="doc-source">來源：GC1991 v1 教學教材 · <a href="{REPO}/blob/main/{source.relative_to(ROOT).as_posix()}">閱讀 Markdown 原文</a> · <a href="../../gc1991-lab/index.html">回到實驗室</a></p></main></div><footer class="site-footer"><div class="wrap footer-inner"><strong>Hydraulic Jump Project</strong><a href="../../index.html">回到專題首頁 ↑</a></div></footer></body></html>'''


def package_lab():
    manifest = json.loads((LAB / 'CHECKSUMS.json').read_text())
    for name, expected in manifest.items():
        actual = hashlib.sha256((LAB / name).read_bytes()).hexdigest()
        if actual != expected:
            raise ValueError(f'Sealed teaching file changed: {name}. Create a reviewed release before repackaging.')
    downloads = ROOT / 'downloads'
    downloads.mkdir(exist_ok=True)
    archive = downloads / 'gc1991-lab-v1.zip'
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as output:
        for name in sorted([*manifest, 'CHECKSUMS.json']):
            info = zipfile.ZipInfo('gc1991-lab/' + name, (2026, 9, 15, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            output.writestr(info, (LAB / name).read_bytes())
    digest = hashlib.sha256(archive.read_bytes()).hexdigest()
    (downloads / 'zip-sha256.txt').write_text(f'{digest}  {archive.name}\n')
    print(f'Packaged {len(manifest)} verified teaching files; ZIP {archive.stat().st_size:,} bytes.')


def stage_site():
    # A separate explicit publication tree excludes virtual environments, local
    # results, Git internals and maintenance sources from the Pages artifact.
    stage = ROOT / '_site'
    if stage.exists():
        shutil.rmtree(stage)
    stage.mkdir()
    for file in ('index.html', '.nojekyll'):
        shutil.copy2(ROOT / file, stage / file)
    for folder in ('assets', 'guides', 'downloads'):
        shutil.copytree(ROOT / folder, stage / folder)
    manifest = json.loads((LAB / 'CHECKSUMS.json').read_text())
    for name in [*manifest, 'CHECKSUMS.json', 'index.html']:
        target = stage / 'gc1991-lab' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(LAB / name, target)
    print('Static Pages artifact is ready in _site/.')


if __name__ == '__main__':
    GUIDES.mkdir(parents=True, exist_ok=True)
    for slug, (title, relative) in PAGES.items():
        (GUIDES / f'{slug}.html').write_text(guide_page(slug, title, LAB / relative))
    package_lab()
    stage_site()
    print(f'Rendered {len(PAGES)} linked Chinese guide pages.')
