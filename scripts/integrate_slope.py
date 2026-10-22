"""Publish a verified offline kit with a separate, concise web reading layer."""
from pathlib import Path
import hashlib,html,json,os,re,shutil,zipfile
ROOT=Path(__file__).resolve().parents[1]
KIT=ROOT/'slope-lab'
SITE=ROOT/'_site'
CONTENT=ROOT/'docs/slope-site'
REVIEW='<aside class="review-strip" role="note">本地審閱稿 · 2026-10-22 · 首頁更新尚未發布</aside>'

def verify_source():
    manifest=json.loads((KIT/'CHECKSUMS.json').read_text())
    for name,digest in manifest.items():
        assert hashlib.sha256((KIT/name).read_bytes()).hexdigest()==digest,name
    archive=ROOT/'downloads/slope-lab-v1.3.zip'
    digest=(ROOT/'downloads/slope-lab-v1.3-sha256.txt').read_text().split()[0]
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==digest
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        for name,digest in manifest.items():
            assert hashlib.sha256(z.read('slope-lab/'+name)).hexdigest()==digest,name
    return manifest

def docs_shell(text,p):
    depth=len(p.relative_to(SITE).parts)-1
    root='../'*depth
    rel=p.relative_to(SITE/'slope-lab/docs')
    back='../'*(len(rel.parts)-1)
    portal=f'''<header class="slope-portal"><div><a class="portal-brand" href="{root}index.html">HJ · 水躍學生專題</a><nav aria-label="全站導覽"><a href="{root}slope-lab/index.html">坡度教材入口</a><a href="{root}research-plan/comparison.html">兩組共同比對</a><a href="{root}downloads/slope-lab-v1.3.zip" download>下載教學包 ↓</a></nav></div></header>'''
    text=text.replace('</head>',f'<link rel="stylesheet" href="{root}assets/slope-portal.css"></head>')
    text=text.replace('<body>','<body>'+portal)
    text=text.replace('完整講義</a>','合併講義</a>')
    text=text.replace('href="../p0_group_a.ipynb"','href="../p0_group_a.ipynb" download')
    text=text.replace('href="../p0_group_b.ipynb"','href="../p0_group_b.ipynb" download')
    text=text.replace('>Notebook檔案：','>下載Notebook：')
    text=text.replace('（在Jupyter中開啟）','（請下載完整教學包後，在Jupyter中開啟；網頁不執行計算）')
    text=text.replace('坡度變化渠道教學包 v1.3 · 2026-10-22','坡度教材 v1.3 · 網站整合 2026-10-22')
    text=text.replace('</footer>',f' · <a href="{root}index.html">回到專題首頁</a></footer>')
    text=text.replace('<div class="scroll">','<div class="scroll" tabindex="0" role="region" aria-label="表格，可左右捲動">')
    text=text.replace('<span class="katex-display">','<span class="katex-display" tabindex="0" role="region" aria-label="公式，可左右捲動">')
    return text

def integrate():
    manifest=verify_source()
    for name in [*manifest,'CHECKSUMS.json']:
        p=SITE/'slope-lab'/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(KIT/name,p)
    for p in sorted((SITE/'slope-lab/docs').rglob('*.html')):
        text=p.read_text()
        name=p.stem
        # Preserve full independent offline prose; shorten only the web layer.
        if p.parent.name=='docs' and (CONTENT/(name+'.html')).exists():
            content=(CONTENT/(name+'.html')).read_text()
            text,n=re.subn(r'(</nav>).*?(<footer>)',lambda m:m[1]+content+m[2],text,count=1,flags=re.S)
            assert n==1,p
        elif name in ['p0_group_a','p0_group_b']:
            start=text.index('<p>P0是一座')
            stop=text.index('<h2>操作目錄</h2>',start)
            recap='<p class="box">本頁直接跟做P0。尚未讀過渠道與邊界，請先看<a href="problem.html">問題設定</a>；SS、SV、B的全名與方程見<a href="methods.html">方法講義</a>。以下操作保持原P0物理參數，並使用指定的數值設定。</p>'
            text=text[:start]+recap+text[stop:]
        elif name=='group_a':
            start=text.index('<p class="box">')
            stop=text.index('<h2>步驟2',start)
            text=text[:start]+'<p class="lead">完成<a href="p0_group_a.html">第一組P0示範</a>後，依本頁計算自己的低、高水準。研究因子與精確設定見<a href="design.html">案例設計</a>。</p>'+text[stop:]
            text=text.replace('步驟2：','步驟1：').replace('步驟3：','步驟2：').replace('步驟4：','步驟3：')
        elif name=='handbook':
            text=text.replace('坡度變化渠道水躍：獨立教學講義','坡度變化渠道水躍：四章合併講義')
        p.write_text(docs_shell(text,p))
    # Runtime acceptance is separately versioned; do not change the tested ZIP.
    acceptance = ROOT/'docs/verification/slope-wsl-2026-10-22'
    if acceptance.exists():
        shutil.copytree(acceptance, SITE/'verification/slope-wsl', dirs_exist_ok=True)
        summary_path = acceptance/'summary.json'
        runtime = json.loads(summary_path.read_text()) if summary_path.exists() else {}
        passed = runtime.get('WSL_runtime_verified') is True
        if passed:
            # Update the web reading layer only; the tested release stays sealed.
            replacements = {
                '本版的本機檢查與尚待 WSL 實跑項目見':
                '本版已完成的 Windows／WSL 實測與 HEC 待辦見',
                '本示範Python部分已在製作環境執行；新版WSL與HEC-RAS 6.6實機驗收尚待完成。':
                '本示範Python部分已在Windows／WSL完成實測；HEC-RAS 6.6實機求解仍待驗收。',
                '新版仍未在Windows／WSL執行，Windows檔案總管搬移與HEC計算也待實機預試，不能將舊GC1991的WSL通過當成本版結果。':
                '同一v1.3 ZIP其後已在Windows／WSL完成安裝、兩組P0 Python流程、Windows連線及專案檔案往返檢查。HEC6.6求解與人工介面操作仍待驗收；詳見本頁上方的實測附錄。',
                '<td>新版Windows／WSL與Windows原生Python</td><td>尚未實際執行</td>':
                '<td>新版Windows／WSL與Windows原生Python</td><td>WSL其後已通過實測；Windows原生Python未測</td>',
                '<td>Windows瀏覽器、檔案總管及HEC-RAS 6.6</td><td>尚待實機驗收</td>':
                '<td>Windows連線、檔案交換及HEC-RAS 6.6</td><td>自動HTTP連線與檔案往返通過；人工GUI及HEC求解未測</td>',
            }
            for page in (SITE/'slope-lab/docs').rglob('*.html'):
                text = page.read_text()
                for old, new in replacements.items():
                    text = text.replace(old, new)
                page.write_text(text)
        for name in ['start', 'verification']:
            page = SITE/'slope-lab/docs'/f'{name}.html'
            text = page.read_text()
            message = '實測通過：原GC1991環境接續安裝、兩組P0 Python、Windows連線與檔案交換。HEC6.6求解仍待驗收。' if passed else '與原 macOS 檢查分開保存，請以紀錄中的執行狀態為準。'
            note = '<p class="box note"><a href="../../verification/slope-wsl/index.html">本次 Windows／WSL 實際驗收紀錄</a>：'+message+'</p>'
            text = text.replace('</h1>', '</h1>'+note, 1)
            page.write_text(text)
    # The manifest certifies the offline archive, not the web reading layer.
    (SITE/'slope-lab/CHECKSUMS.json').unlink()
    # Website landing is separate from the frozen teaching archive.
    (SITE/'slope-lab/index.html').write_text(landing())
    if os.environ.get('SITE_REVIEW')=='1':
        for p in SITE.rglob('*.html'):
            text=p.read_text().replace('<body>','<body>'+REVIEW,1)
            p.write_text(text)
    print(f'Integrated slope kit: {len(manifest)} preserved source files; web navigation and concise reading layer.')

def landing():
    content='''<p class="eyebrow">SLOPE CHANNEL / P0</p><h1>坡度變化渠道教學</h1><p class="lead">從問題設定到自己的研究案例。選一條閱讀路線與一條操作路線，不需要在不同頁面反覆尋找相同參數。</p>
<div class="resource-grid">
<a class="resource" href="docs/index.html"><h2>讀講義</h2><p>四章依序說明問題、方法、案例與結果；也可合併閱讀／列印。</p><span>開啟教材目錄 →</span></a>
<a class="resource" href="docs/p0_demo.html"><h2>跟做P0</h2><p>第一組9步、第二組10步，附逐格Notebook、參考圖及判讀。</p><span>選擇組別示範 →</span></a>
<a class="resource" href="../downloads/slope-lab-v1.3.zip" download><h2>下載與計算</h2><p>已完成GC1991者沿用原Windows／WSL，加裝v1.3後執行；網站提供閱讀，不在瀏覽器內跑模式。</p><span>下載ZIP ↓</span></a></div>
<h2>接下來做什麼？</h2><ol><li><a href="docs/start.html">從GC1991接續安裝</a>，兩組都在原Ubuntu執行Python，再重現P0。</li><li>確認<a href="../research-plan/group-1.html">第一組</a>或<a href="../research-plan/group-2.html">第二組</a>的個人分工。</li><li>依<a href="docs/design.html">案例設計</a>與個人操作單完成低、高水準。</li><li>閱讀<a href="docs/results.html">結果判讀</a>，按<a href="docs/submission.html">繳交格式</a>整理證據。</li></ol>
<div class="notice">Windows／WSL已完成兩組P0 Python流程與檔案交換；<strong>HEC-RAS 6.6實際計算仍待驗收。</strong>B波動的網格穩定性保留為研究內容。<a href="docs/verification.html">查看完整範圍</a>。</div>
<p><a href="docs/glossary.html">縮寫與符號</a> · <a href="docs/sources.html">來源與授權</a> · <a href="../downloads/slope-lab-v1.3-sha256.txt">下載檔指紋</a> · <a href="../gc1991-lab/index.html">GC1991驗證教材</a></p>'''
    return '''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>坡度變化渠道教材｜水躍學生專題</title><link rel="icon" href="../assets/favicon.svg"><link rel="stylesheet" href="../assets/site.css"><script defer src="../assets/site.js"></script></head><body><a class="skip" href="#main">跳到主要內容</a><header class="site-header"><div class="wrap header-inner"><a class="brand" href="../index.html"><span class="mark">HJ</span><strong>水躍學生專題</strong></a><button class="menu-toggle" type="button" aria-expanded="false" aria-controls="site-nav">選單</button><nav class="nav" id="site-nav" aria-label="主要導覽"><a href="../index.html">專題首頁</a><a href="docs/p0_demo.html">P0示範</a><a href="../research-plan/comparison.html">共同比對</a></nav></div></header><main id="main" class="wrap section">'''+content+'''</main><footer class="site-footer"><div class="wrap footer-inner"><p>坡度教學包v1.3 · 網站整合2026-10-22</p><a href="../index.html">回到專題首頁</a></div></footer></body></html>'''
