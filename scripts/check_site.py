"""Check the actual GitHub Pages artifact and the sealed teaching download."""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import hashlib
import json
import re
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / '_site'


class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.refs, self.ids, self.h1 = [], set(), 0
        self.lang, self.has_title = None, False
        self.feed(path.read_text())

    def handle_starttag(self, tag, pairs):
        attrs = dict(pairs)
        if tag == 'html': self.lang = attrs.get('lang')
        if tag == 'title': self.has_title = True
        if tag == 'h1': self.h1 += 1
        if 'id' in attrs:
            assert attrs['id'] not in self.ids, f'Duplicate id: {attrs["id"]}'
            self.ids.add(attrs['id'])
        for key in ('href', 'src'):
            if key in attrs: self.refs.append(attrs[key])
        if tag == 'img': assert attrs.get('alt'), 'Image lacks alternative text'


def main():
    pages = {path: Page(path) for path in SITE.rglob('*.html')}
    count = 0
    for path, page in pages.items():
        assert page.lang == 'zh-Hant' and page.has_title and page.h1 == 1, path
        for ref in page.refs:
            url = urlsplit(ref)
            if url.scheme or url.netloc: continue
            assert not url.path.startswith('/'), f'Root-relative URL breaks project hosting: {path}: {ref}'
            target = (path.parent / unquote(url.path)).resolve() if url.path else path
            assert SITE.resolve() in target.parents, f'Outside site: {ref}'
            if target.is_dir(): target /= 'index.html'
            assert target.is_file(), f'Missing target: {path.relative_to(SITE)} -> {ref}'
            if url.fragment and target in pages:
                assert unquote(url.fragment) in pages[target].ids, f'Missing anchor: {ref}'
            count += 1
    methods = (SITE / 'guides/gc1991/methods.html').read_text()
    source = (ROOT / 'gc1991-lab/docs/methods.md').read_text()
    display_count = len(re.findall(r'^\$\$$', source, re.M)) // 2
    assert display_count > 0
    assert methods.count('class="math-display"') == display_count
    # TeX must survive Markdown byte-for-byte, including matrix line breaks.
    from html import escape
    for equation in re.findall(r'\$\$(.*?)\$\$', source, re.S):
        assert '\\[' + escape(equation) + '\\]' in methods, equation
    assert 'class="math-inline"' in methods
    assert 'EQUATIONPLACEHOLDER' not in methods
    manifest = json.loads((ROOT / 'gc1991-lab/CHECKSUMS.json').read_text())
    archive = SITE / 'downloads/gc1991-lab-v1.zip'
    with zipfile.ZipFile(archive) as bundle:
        assert bundle.testzip() is None
        expected_names = {'gc1991-lab/' + name for name in [*manifest, 'CHECKSUMS.json']}
        assert set(bundle.namelist()) == expected_names
        for name, digest in manifest.items():
            assert hashlib.sha256(bundle.read('gc1991-lab/' + name)).hexdigest() == digest, name
    digest = (SITE / 'downloads/zip-sha256.txt').read_text().split()[0]
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == digest
    assert not list(SITE.rglob('.git')) and not list(SITE.rglob('.venv'))
    print(f'PASS: {len(pages)} pages, {count} local references, {display_count} display equations, {len(manifest)} sealed teaching files and ZIP checksum.')


if __name__ == '__main__': main()
