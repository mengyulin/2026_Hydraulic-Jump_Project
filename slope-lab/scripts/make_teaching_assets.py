"""Build an undergraduate handbook and offline LaTeX guides; preserve solver/code cells."""
from pathlib import Path
import csv
import hashlib
import html
import json
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from case_tools import load_case,bed_z
SRC=ROOT/'docs/source'
STYLE=(SRC/'style.css').read_text(encoding='utf-8')
CACHE={}
MATH=re.compile(r'\\\[(.*?)\\\]|\\\((.*?)\\\)',re.S)
COUNTS={}


def render_math(body):
    specs=[(html.unescape(m.group(1) if m.group(1) is not None else m.group(2)),m.group(1) is not None) for m in MATH.finditer(body)]
    missing=list(dict.fromkeys(x for x in specs if x not in CACHE))
    if missing:
        result=subprocess.run(['node',str(ROOT/'scripts/render_math.cjs')],input=json.dumps([dict(tex=t,display=d) for t,d in missing]),text=True,capture_output=True,check=True)
        CACHE.update(zip(missing,json.loads(result.stdout)))
    return MATH.sub(lambda m:CACHE[(html.unescape(m.group(1) if m.group(1) is not None else m.group(2)),m.group(1) is not None)],body)


def page(title,body,asset_prefix=None):
    # Compatibility for the separate historical teacher-report builder.
    mathcss='' if asset_prefix is None else f'<link rel="stylesheet" href="{asset_prefix}vendor/katex/dist/katex.min.css">'
    return '<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+html.escape(title)+'</title>'+mathcss+'<style>'+STYLE+'</style></head><body><main><h1>'+html.escape(title)+'</h1>'+body+'</main></body></html>'


def table(head,rows):
    e=lambda x:html.escape(str(x))
    return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+e(x)+'</th>' for x in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+e(x)+'</td>' for x in r)+'</tr>' for r in rows)+'</tbody></table></div>'


def write(name,title,body):
    p=ROOT/'docs'/name;p.parent.mkdir(parents=True,exist_ok=True)
    back='../'*(len(Path(name).parts)-1)
    nav='<nav aria-label="教材目錄">'+''.join(f'<a href="{back}{f}.html">{s}</a>' for f,s in [('index','教材入口'),('handbook','完整講義'),('problem','問題設定'),('methods','三種方法'),('design','案例分工'),('results','結果判讀'),('p0_demo','P0操作示範'),('glossary','符號表')])+'</nav>'
    footer=f'<footer>坡度變化渠道教學包 v1.3 · 2026-10-22 · 方程式由LaTeX預先排版，離線可讀。<a href="{back}sources.html">來源與授權</a> · <a href="{back}verification.html">驗證範圍</a></footer>'
    COUNTS[name]=len(list(MATH.finditer(body)))
    p.write_text(page(title,nav+render_math(body)+footer,back+'../'),encoding='utf-8')


FAMILIES=[
 ('上游坡度與入流福祿數',r'\(\mathrm{Fr}_{\mathrm{in}}=1.5,2,2.5\)','改變上游坡度S₁，以正常水深得到不同入口福祿數。','入口Fr變大，水躍是否往下游移？躍前Fr是否仍等於入口Fr？'),
 ('下游尾水',r'\(h_{\mathrm{out}}/h_{\mathrm{out},0}=0.95,1,1.05\)','只改出口指定水深，保留幾何、流量與粗糙度。','尾水升高後，水躍是否往上游移？局部峰高與外側水深是否有相同趨勢？'),
 ('平滑轉折長度',r'\(L_t=1,2,4\,\mathrm{m}\)','改轉折長度，中心12 m與兩端坡度保持不變。','坡度較緩慢地轉換，是否減少局部水面變化？位置與波尾是否有不同反應？'),
 ('下游坡度',r'\(S_2/S_{2,0}=0.5,1,2\)','改下游坡度，但出口床高與指定尾水深固定。','下游坡度改變如何影響回水與水躍位置？不要把出口改成正常水深。'),
 ('Manning粗糙度',r'\(n=0.007,0.008,0.009\,\mathrm{s\,m^{-1/3}}\)','改整段渠道粗糙係數，入口正常水深會一起重算。','摩阻增大與入口速度改變各如何影響結果？不要為了消波而校正n。')]


def dynamic():
    c=load_case();vals=[
      ['渠道長度',r'\(L\)','30 m'],['矩形渠寬',r'\(W\)','0.46 m'],['總流量',r'\(Q\)','0.05413786 m³/s'],
      ['單位寬流量',r'\(q=Q/W\)','0.117691 m²/s'],['重力加速度',r'\(g\)','9.81 m/s²'],
      ['Manning粗糙係數',r'\(n\)',r'\(0.008\,\mathrm{s\,m^{-1/3}}\)'],
      ['上游坡度',r'\(S_1\)',f"{c['S1']:.15f}"],['下游坡度',r'\(S_2\)',f"{c['S2']:.15f}"],
      ['轉折中心／長度',r'\(x_c,L_t\)','12 m／2 m'],['出口渠底高程',r'\(z_b(L)\)','0 m'],
      ['入口正常水深',r'\(h_{\mathrm{in}}\)',f"{c['hin_m']:.9f} m"],['出口指定水深',r'\(h_{\mathrm{out}}\)',f"{c['hout_m']:.9f} m"],
      ['收縮／擴張係數',r'\(C_c,C_e\)','0／0']]
    methodrows=[['SS','Standard-step method／標準步法','定常能量計算＋比力跳接','水面分支、局部跳接位置；不算物理水躍長度'],
                ['SV','Saint-Venant equations／聖維南淺水方程','深度平均、靜水壓、非穩態','水深隨時間演變、平均水面與波動'],
                ['B','Boussinesq型模型／本套件的定常壓力近似','加入部分非靜水壓修正','定常水面與模型波列；非完整非穩態波浪模型'],
                ['HEC-RAS 6.6',"Hydrologic Engineering Center's River Analysis System／河川分析系統",'本案選一維定常混合流','與Python標準步法配對的工程計算']]
    cases=[]
    for name in ['P0']+[f'P{i}{s}' for i in range(1,6) for s in 'LH']:
        d=load_case(name);cases.append([name,f"{d['S1']:.8f}",f"{d['S2']:.8f}",d['n'],d['transition_length_m'],f"{d['hin_m']:.6f}",f"{d['hout_m']:.6f}",f"{d['Fr_in']:.4f}"])
    outputs=[['case.json','本次真正使用的物理條件','查幾何、流量、粗糙度與邊界'],['metadata.json','數值設定、程式識別與執行狀態','先看成功／失敗，再看定常篩檢'],['profile.csv','統一欄位的水面表','繪完整與局部水面'],['summary.json','位置、水深及波動指標','保留定義與N/A原因'],['native/','原程式的輸入、日誌與收支','檢查負水深、流量收支及時間變化；SS無此資料夾'],['newton.json（B）','逐級固定點搜尋記錄','確認殘差與每一級是否通過'],['solution.json（SS）','標準步法分支與跳接','追溯有效分支與能量殘差']]
    hecf=[['River Station','river_station','沿程斷面站號，本案從30遞減至0'],['W.S. Elev','water_surface_m','水面高程，m'],['Froude # Chl','Fr','主槽福祿數，無因次'],['Q Total','Q_m3_s','總流量，m³/s']]
    files=[['.prj','專案入口，HEC-RAS由此開啟'],['.g01','渠道幾何、斷面及粗糙度'],['.f01','定常流量及上下游邊界'],['.p01','求解計畫與選項'],['expected.json／sections.csv','預期設定與實際寫入的斷面數值'],['paired_ss.csv','由相同寫入數值重算的Python結果，不是HEC輸出']]
    return dict(P0_TABLE=table(['項目','符號','P0設定'],vals),METHOD_TABLE=table(['簡稱','完整名稱','主要假設／方式','本專題用途'],methodrows),
       FAMILY_TABLE=table(['同編號學生','系列','變動因子與三個水準','固定／連動條件'],[[f'A{i}／B{i}',f'P{i}',f'{v[0]}：{v[1]}',v[2]] for i,v in enumerate(FAMILIES,1)]),
       CASE_TABLE=table(['案例','上游S₁','下游S₂','n','Lt (m)','入口h (m)','出口h (m)','入口Fr'],cases),
       GRID_TABLE=table(['N','間距Δx (m)','用途'],[[n,f'{30/n:.7f}','起步檢查' if n==512 else '主要比較'] for n in [512,1024,2048]]),
       OUTPUT_TABLE=table(['檔案','內容','學生要讀什麼'],outputs),HEC_FIELDS=table(['HEC欄名','CSV表頭','意義與單位'],hecf),HEC_FILES=table(['檔案','用途'],files),
       ASSIGNMENT_LINKS='<div class="assignment-links">'+''.join(f'<a href="assignments/{g}{i}.html">{g}{i}：{FAMILIES[i-1][0]}</a>' for g in 'AB' for i in range(1,6))+'</div>')


def schematic():
    c=load_case();p=ROOT/'reference/ss_P0_dx0025.csv'
    with p.open(encoding='utf-8') as f:r=list(csv.DictReader(f))
    X=lambda x:65+735*x/30;Y=lambda z:285-z*950
    bed=' '.join(f'{X(i/10):.2f},{Y(bed_z(i/10,c)):.2f}' for i in range(301))
    water=' '.join(f"{X(float(a['x_m'])):.2f},{Y(float(a['z_m'])+float(a['h_m'])):.2f}" for a in r)
    svg=f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1120 385" role="img" aria-labelledby="title desc"><title id="title">P0坡度變化渠道與矩形斷面</title><desc id="desc">入口在左，出口在右；坡度於11至13公尺轉換。藍線為標準步法參考水面，灰線為渠底。</desc><defs><marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M 0 0 L 10 5 L 0 10 z" fill="#285668"/></marker></defs><rect width="1120" height="385" fill="#f3f8fa"/><g font-family="system-ui,sans-serif" font-size="17" fill="#193346"><text x="35" y="35" font-size="21">縱剖面：上游陡、下游緩</text><rect x="{X(11)}" y="55" width="{X(13)-X(11)}" height="230" fill="#e2ebcd"/><polyline points="{bed}" fill="none" stroke="#707b7e" stroke-width="3"/><polyline points="{water}" fill="none" stroke="#167a9b" stroke-width="3"/><path d="M80 65 H220" stroke="#285668" stroke-width="2" marker-end="url(#arrow)"/><text x="85" y="53">流向／固定流量 Q</text><text x="80" y="145">入口正常水深</text><text x="605" y="110">出口指定尾水</text><text x="145" y="255">陡坡 S₁</text><text x="580" y="265">緩坡 S₂</text><path d="M65 316 H800" stroke="#285668" marker-end="url(#arrow)"/><text x="60" y="341">0</text><text x="{X(11)-18}" y="307">11</text><text x="{X(13)-2}" y="307">13</text><text x="765" y="341">30 m</text><text x="410" y="340">x 向下游增加</text><text x="295" y="79">平滑轉折</text><text x="35" y="370" font-size="14">水面高程＝渠底高程＋當地水深；縱向比例放大。</text><text x="880" y="35" font-size="21">矩形橫斷面</text><path d="M895 100 V285 H1070 V100" fill="none" stroke="#707b7e" stroke-width="5"/><rect x="898" y="155" width="169" height="127" fill="#d7edf3"/><path d="M895 155 H1070" stroke="#167a9b" stroke-width="3"/><path d="M990 164 V276" stroke="#285668" marker-start="url(#arrow)" marker-end="url(#arrow)"/><text x="1005" y="228">h</text><path d="M902 315 H1063" stroke="#285668" marker-start="url(#arrow)" marker-end="url(#arrow)"/><text x="925" y="345">W＝0.46 m</text><text x="865" y="80" font-size="15">h 從當地渠底向上量</text></g></svg>'''
    p=ROOT/'docs/assets/channel.svg';p.parent.mkdir(exist_ok=True);p.write_text(svg,encoding='utf-8')


def glossary():
    rows=[['SS','Standard-step method','標準步法，以能量式逐斷面計算，再用比力跳接'],['SV','Saint-Venant equations','聖維南一維淺水方程；本案使用靜水壓假設'],['B','Boussinesq-type model','本套件特指定常壓力近似的Boussinesq型模型'],['HEC-RAS',"Hydrologic Engineering Center's River Analysis System",'美國陸軍工兵團的河川分析系統；本案6.6版'],['CFL','Courant–Friedrichs–Lewy','控制時間更新步長的慣用數值參數'],['PDE','Partial differential equation','偏微分方程，描述量隨空間／時間的變化'],['SI','International System of Units','國際單位制；本教材用m、s、m³/s'],['WSL','Windows Subsystem for Linux','Windows上的Linux環境，第一組Windows電腦使用'],['CSV','Comma-separated values','以逗號分欄的文字表格'],['JSON','JavaScript Object Notation','儲存參數名稱與數值的文字格式'],['N/A／null','未定義／不適用／無足夠資料','不是零；必須說明原因']]
    symbols=[(r'x,L','沿程座標、渠道總長','m'),(r'W','矩形渠寬；避免與B模型混用','m'),(r'z_b,h,\eta','床面高程、水深、水面高程','m'),(r'Q,q','總流量、單位寬流量','m³/s、m²/s'),(r'u,g','斷面平均速度、重力加速度','m/s、m/s²'),(r'A,P_w,R','通水面積、濕周、水力半徑','m²、m、m'),(r'n','Manning粗糙係數',r'\(\mathrm{s\,m^{-1/3}}\)'),(r'S_0,S_1,S_2,S_f','當地床坡、上游床坡、下游床坡、摩阻坡度','無因次'),(r'x_c,L_t','坡度轉折中心、轉折長度','m'),(r'h_n,h_c','正常水深、臨界水深','m'),(r'\mathrm{Fr}','福祿數','無因次'),(r'h_1,h_2','躍前、躍後水深，不必等於兩端邊界水深','m'),(r'H,\Delta E_J','工程水頭、經典局部水躍損失水頭','m'),(r'M','單位寬比力','m²'),(r'x_J,x_{50}','比力跳接位置、50%參考水深上穿位置','m'),(r'N,\Delta x','單元／區間數、網格間距','個數、m'),(r't,\tau','SV物理時間、B鬆弛推進時間','s、演算時間參數'),(r'\lambda,\kappa','B數值耗散倍率、額外濾波係數','無因次'),(r'\Lambda,\ell_d','波峰間距、振幅衰減尺度','m'),(r'\Pi_B,P_{b,B}','非靜水壓通量修正、床面壓力修正（均除以密度）','m³/s²、m²/s²')]
    return '<p>先查縮寫，再查符號。符號只在本教材的定義下使用；尤其注意小寫 \\(\\lambda\\) 與大寫 \\(\\Lambda\\)、學生B組與B模型的差別。</p><h2>縮寫與名稱</h2>'+table(['縮寫','完整名稱','本專題的意思'],rows)+'<h2>符號、意義及單位</h2>'+table(['符號','意義','單位'],[[r'\('+a+r'\)',b,c] for a,b,c in symbols])+'<p>下標in/out代表入口／出口，up/down代表上游／下游取樣區；fine/coarse代表細／粗網格；下標x與xx表示一次、二次空間微分。</p>'


def assignments():
    for g in 'AB':
        for i,(topic,levels,fixed,question) in enumerate(FAMILIES,1):
            ids=['P0',f'P{i}L',f'P{i}H'];rs=[]
            for name in ids:
                c=load_case(name);rs.append([name,f"{c['S1']:.8f}",f"{c['S2']:.8f}",c['n'],c['transition_length_m'],f"{c['hin_m']:.6f}",f"{c['hout_m']:.6f}",f"{c['Fr_in']:.3f}"])
            methods='標準步法（Standard-step method，SS）、聖維南淺水方程（Saint-Venant，SV）及定常壓力近似Boussinesq型模型（B）' if g=='A' else "Python標準步法（Standard-step method，SS）與HEC-RAS 6.6（Hydrologic Engineering Center's River Analysis System）"
            tasks=r'每案標準步法做斷面0.125、0.05、0.025 m；SV與B先做512起步，再做1024、2048。選一個個人變體做四項控制：SV半CFL、B半CFL、B2048的\(\lambda=2\)及B off。CFL控制時間步，\(\lambda\)控制數值耗散；詳見第一組操作頁。' if g=='A' else '每案做斷面0.5、0.25、0.125 m，Python與HEC使用相同斷面及寫入數值。逐次保存HEC版本、計算訊息、警告、原始匯出與跳接區間；詳見第二組操作頁。'
            body=f'<p class="lead">你的研究問題：{question}</p><p>本專題使用長30 m、寬0.46 m、上游陡下游緩的矩形渠道。入口按實際坡度求正常水深，出口指定尾水；共同總流量0.05413786 m³/s，收縮／擴張係數均為0。先讀<a href="../problem.html">完整問題設定</a>。</p><p>你使用的方法是{methods}。你的跨組搭檔為{("B" if g=="A" else "A")}{i}，研究相同條件。</p><h2>1. 你的三個條件</h2><p>{topic}的水準：{levels}。{fixed}低、高水準的L/H是案例編號，不是結果大小的保證。</p>'+table(['案例','上游坡度','下游坡度','n','轉折長m','入口深m','出口深m','入口Fr'],rs)+f'<h2>2. 開始前先做預測</h2><p>用一段文字寫出低水準到高水準時，水躍可能往哪裡移、哪個水深可能變化。列出你的理由及可能反例；之後用計算修正解釋。</p><h2>3. 依序完成計算</h2><p>{tasks}</p><p>P0可共用組內驗收，但須能解釋。主結果使用實際座標的水面高程 \\(\\eta=z_b+h\\)。詳見<a href="../group_{g.lower()}.html">你的組別操作頁</a>。</p><h2>4. 每案的自查</h2><ul><li>物理參數與上表一致，初始條件與數值設定有記錄。</li><li>完整水面從入口連到出口；執行失敗保留日誌。</li><li>水躍位置定義寫清楚，多重交越不強行選成唯一位置。</li><li>先比較參數趨勢，再比較解析度；未穩定的波動保留說明。</li></ul><h2>5. 你的繳交成果</h2><p>三條件表、完整與局部水面、位置及外側水深趨勢、數值敏感度、方法專屬記錄，以及一頁有證據的結論。填寫<a href="../submission.html">繳交模板</a>，不只交截圖。</p>'
            write(f'assignments/{g}{i}.html',f'{g}{i}個人操作單：{topic}',body)


def verification():
    d=json.loads((ROOT/'reference/teaching_acceptance.json').read_text());rows=[]
    for r in d['P0']['checks']:
        label={'ss':'標準步法（SS）','sv':'聖維南模型（SV）','b':'定常壓力近似模型（B）'}[r['method']]
        label+=('，斷面0.025 m' if r['N'] is None else f"，N={r['N']}")
        rows.append([label,f"{r['max_depth_difference_m']:.3e}",f"{r['tolerance_m']:.0e}",'通過'])
    return r'''<p class="lead">本頁說明哪些檢查已完成，以及結果可以支持到什麼程度。v1.1重寫教學文件；v1.2新增P0逐步示範並重跑其Python流程；v1.3改為從既有GC1991的Windows／WSL環境接續安裝，補充檔案交換與環境檢查。數值核心與物理參數不變，不宣稱新的物理驗證。</p><h2>1. P0數值重現</h2><p>使用相同條件重新執行標準步法（SS）、聖維南模型（SV）與定常壓力近似Boussinesq模型（B），在相同網格逐點比對水深，沒有水平平移。</p>'''+table(['方法','最大水深差m','重現容許值m','結果'],rows)+r'''<p>小差值表示新版介面可重現原有計算；不表示模型對實驗同樣精確。P0重現明確使用原uniform初場。兩份Notebook實際執行、獨立資料夾重新編譯及P0重算均完成；十個變體的SV/B 512起步與五項控制共25次通過完整性檢查。</p><h2>2. 尚不能說成「全部收斂」</h2><p>SV512的前後半平均最大差約2.102 mm，局部最大時間標準差約1.147 mm，仍未通過嚴格定常篩檢。B1024與2048的波峰明顯不同；B2048有多重90%上穿點，所以唯一上升寬度未定義。這些都是學生可以分析的結果。</p><p>早期uniform粗網格啟動在部分變體產生負水深，失敗紀錄由教師保留。學生介面預設tanh平滑初場；P0驗收保留原初場，兩者在文件中明確區分。</p><h2>3. HEC與Windows的狀態</h2><p>HEC-RAS 6.6的三份P0輸入完成文字欄位與幾何核對；CSV比較器以標明為合成的資料測試過。製作環境沒有HEC引擎，尚未實際開檔／計算；v1.3已核對兩套教材的Basilisk來源相同、Linux編譯分支、Python依賴、共用程式庫與Windows CSV格式；本機macOS驗收另見下方記錄。新版仍未在Windows／WSL執行，Windows檔案總管搬移與HEC計算也待實機預試，不能將舊GC1991的WSL通過當成本版結果。教師需依<a href="hec66.html">實機操作頁</a>完成檢查，並保存<a href="../templates/windows_wsl_acceptance.org">Windows／WSL驗收表</a>。</p><h2>4. 原始驗收證據</h2><p><a href="../reference/teaching_acceptance.json">機器可讀驗收摘要</a>、<a href="../reference/tested-python-packages.txt">測試時的Python套件版本</a>、<a href="../reference/source_provenance.json">來源雜湊</a>。雜湊是檔案內容的數位指紋，用來辨認程式版本；學生主要看物理與數值設定，附錄保留完整追溯資訊。</p>'''


def compatibility():
    source=ROOT/'reference/compatibility_v1_3.json'
    if not source.exists():return ''
    data=json.loads(source.read_text())
    rows=[['全新隔離安裝／編譯','macOS；通過，6項快速測試'],
          ['兩組P0 Notebook','Python流程通過；HEC輸入與待填狀態不代替實跑'],
          ['兩組啟動指令','本機Jupyter與Slope Channel Lab核心通過'],
          ['Windows文字交換格式','3種間距的UTF-8 BOM／CRLF合成資料通過；非HEC輸出'],
          ['Linux x86-64／Python 3.12套件','目標輪檔可取得；不是Linux安裝或執行'],
          ['新版Windows／WSL與Windows原生Python','尚未實際執行'],
          ['Windows瀏覽器、檔案總管及HEC-RAS 6.6','尚待實機驗收']]
    p0=table(['本次重算','與舊參考最大水深差m','重現檢查'],[[v['method'],f"{v['max_depth_difference_m']:.3e}",'通過' if v['passed'] else '未通過'] for v in data['P0_reproduction']])
    return '<h2>5. v1.3接續安裝的相容性檢查（2026-10-22）</h2><p>在全新資料夾重新安裝套件、編譯、執行兩份P0 Notebook及啟動服務；測試平台是macOS，不是Windows。數值核心、物理設定與四份Notebook計算格沿用v1.2。</p>'+table(['項目','證據範圍'],rows)+p0+'<p>Linux輪檔解析在macOS指定目標平台完成，pip的條件式依賴仍可能採宿主資訊，不能替代Ubuntu實裝。環境檢查器會拒絕把macOS當成WSL通過。<a href="../reference/compatibility_v1_3.json">完整相容性摘要</a>；實機操作與驗收指令見<a href="start.html#acceptance">接續安裝頁第8步</a>。</p>'


def notebooks():
    intros={
      'student_lab.ipynb':[
       r'''# 第一組：坡度變化渠道的三種計算方法
本筆記本計算長30 m、寬0.46 m的矩形渠道：上游陡、下游緩，固定總流量，入口採正常水深，出口採指定尾水。先閱讀 [問題設定](docs/problem.html) 與 [方程式講義](docs/methods.html)。
SS是Standard-step method（標準步法）；SV是Saint-Venant（聖維南淺水方程）；B是本套件的定常壓力近似Boussinesq型模型。B的波動仍待研究。
水面圖統一使用 $\eta=z_b+h$；流速與流量關係為 $q=Q/W=hu$。P0是共同基準，每人再做自己的低、高水準。
## 步驟1：選案例並讀參數
下方選P0開始。`S1/S2`是兩段床坡，`n`是Manning粗糙係數，`hin_m/hout_m`是兩端水深，`Fr_in`是入口福祿數。Shift+Enter執行後再往下。''',
       r'''## 步驟2：執行共同基準
P0採原uniform初場以便重現；個人變體採tanh平滑初場。SS斷面間距0.025 m，SV用512單元，B用1024區間；這是第一次操作，不是全部網格比較。
每次都會新建`runs`資料夾。請等待完成並保留資料。''',
       r'''## 步驟3：比較水面高程
下圖畫 $\eta=z_b+h$，附渠底；完整圖查邊界，局部圖看水躍與波動。SS是定常跳接、SV是200–300秒平均，B是固定點續算後水面。不同狀態不要混稱同一瞬間。''',
       r'''## 步驟4：讀指標而不只看圖
`x50_unique_m`是唯一的50%參考水深上穿位置；多個交點時為null，須查看`all_upcrossings_m`。`first_peak_h_m`是水深峰值，`first_peak_x_m`是位置；尾波峰距與衰減見 [結果判讀](docs/results.html)。null不是零。''',
       r'''## 步驟5：個人案例與四項控制
先把CASE_ID改成你的PnL/PnH，按 [第一組操作](docs/group_a.html) 完成1024、2048主要計算，再選一個變體做下列控制。CFL控制時間步，$\lambda$控制數值耗散；比較1024、$\lambda=1$與2048、$\lambda=2$近似固定$\lambda\Delta x$。B off關閉同核心非靜水壓修正。
下方開關預設False；確認案例後才改True。'''],
      'group_b.ipynb':[
       r'''# 第二組：Python標準步法與HEC-RAS 6.6
共同問題為30 m長、0.46 m寬的坡度變化矩形渠道，入口正常水深、出口指定尾水。先讀 [問題設定](docs/problem.html)。
SS是Standard-step method（標準步法），以能量式追蹤水面、比力式連接水躍。HEC-RAS全名為Hydrologic Engineering Center's River Analysis System，本專題用6.6的一維定常混合流。
水面高程是 $\eta=z_b+h$；HEC輸入總流量 $Q$，不是單位寬流量$q=Q/W$。
## 步驟1：選擇共同P0
改STUDENT_ID為你的代號，由上往下逐格執行。''',
       r'''## 步驟2：先完成Python斷面敏感度
三次使用斷面間距0.5、0.25、0.125 m。比較水面高程與跳接位置。標準步法的零長度跳接不預測真實水躍長度。''',
       r'''## 步驟3：產生相同條件的HEC專案
每次輸出到新資料夾。兩組Python均可沿用WSL；依 [檔案交換](docs/start.html#exchange) 將整份專案複製到Windows，再用HEC-RAS 6.6開啟各子資料夾的.prj，依 [操作頁](docs/hec66.html) 核對SI單位、入口Normal Depth、出口Known W.S.、Mixed與Average Friction Slope，再Compute。
paired_ss.csv仍是Python結果；本步不會執行HEC或假造其輸出。''',
       r'''## 步驟4：讀入真正的HEC匯出
照 [第二組流程](docs/group_b.html) 保存原表，將River Station、水面高程、福祿數及總流量整理成templates/hec_profile.csv欄位。
修改下方路徑，使CSV與當次專案／間距一致；未提供真實CSV時，此格只顯示待完成訊息。''']}
    for name,texts in intros.items():
        p=ROOT/name;d=json.loads(p.read_text(encoding='utf-8'));code=[c for c in d['cells'] if c['cell_type']=='code'];assert len(code)==len(texts)
        cells=[]
        for i,(c,txt) in enumerate(zip(code,texts)):
            cells.append(dict(cell_type='markdown',id=f'guide-{i}',metadata={},source=txt.splitlines(True)));cells.append(c)
        cells.append(dict(cell_type='markdown',id='guide-submit',metadata={},source=['## 下一步與繳交\n依 [繳交格式](docs/submission.html) 保存參數、原始結果、圖與指標。完成數值重現不代表波動已收斂；沒有唯一指標時，說明N/A原因。']))
        d['cells']=cells;p.write_text(json.dumps(d,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')


def main():
    replacements=dynamic();schematic();bodies={}
    (ROOT/'templates/report.org').write_text((SRC/'report_template.org').read_text(encoding='utf-8'),encoding='utf-8')
    titles={'index':'坡度變化渠道：大學生專題教材','problem':'第一章　問題設定與水理基礎','methods':'第二章　三種計算方法與方程式','design':'第三章　案例設計與十人分工','results':'第四章　如何判讀水面與收斂趨勢','start':'從GC1991接續：Windows／WSL安裝與檔案交換','group_a':'第一組操作：標準步法、聖維南與Boussinesq型模型','group_b':'第二組操作：標準步法與HEC-RAS 6.6','hec66':'HEC-RAS 6.6逐項操作與核對','submission':'成果報告與可重跑資料的繳交方式'}
    for name,title in titles.items():
        text=(SRC/(name+'.html.in')).read_text(encoding='utf-8')
        for key,value in replacements.items():text=text.replace('{{'+key+'}}',value)
        assert '{{' not in text,name
        bodies[name]=text;write(name+'.html',title,text)
    book='<p class="box"><a href="p0_demo.html">新增：P0兩組完整操作示範（參數設定、計算、繪圖與判讀）</a></p><p class="lead">從問題設定開始，依序理解方法、規劃計算與解讀結果。全份講義不需先前研究對話；操作與繳交頁另有完整步驟。</p><ol>'+''.join(f'<li><a href="#chapter-{key}">{titles[key]}</a></li>' for key in ['problem','methods','design','results'])+'</ol>'
    for key in ['problem','methods','design','results']:
        book+=f'<section class="chapter" id="chapter-{key}"><h2 class="chapter-title">{titles[key]}</h2>'+bodies[key]+'</section>'
    write('handbook.html','坡度變化渠道水躍：獨立教學講義',book)
    write('glossary.html','縮寫、符號與單位查詢',glossary());assignments();notebooks()
    write('verification.html','數值重現、驗證範圍與已知限制',verification()+compatibility())
    provenance=(ROOT/'docs/sources.org').read_text(encoding='utf-8')
    write('sources.html','附錄：來源、版本與授權','<p>本頁供追溯程式與授權，不是初學者必須先讀的操作前提。B為本套件的定常壓力近似Boussinesq模型；SS為標準步法；SV為聖維南淺水方程。GC1991是既有驗證案例的識別碼，S3是本案物理設定的歷史編號；本教材直接稱共同基準P0。</p><pre>'+html.escape(provenance)+'</pre><p>方程式使用LaTeX來源，依<a href="https://katex.org/docs/node">KaTeX官方預先排版說明</a>產生HTML與MathML；本包附固定0.19.0版CSS、字型及MIT授權。閱讀不需Node或網路；重新建置文件才需要Node。<a href="../LICENSES/KaTeX-LICENSE.txt">KaTeX授權</a> · <a href="../vendor/katex/provenance.json">下載來源與雜湊</a></p>')
    from make_p0_walkthrough import build as build_walkthrough
    build_walkthrough(write,table)
    (ROOT/'docs/equation_counts.json').write_text(json.dumps(COUNTS,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Built',len(COUNTS),'offline teaching pages;',sum(COUNTS.values()),'LaTeX expressions;',len(CACHE),'distinct expressions.')


if __name__=='__main__':main()
