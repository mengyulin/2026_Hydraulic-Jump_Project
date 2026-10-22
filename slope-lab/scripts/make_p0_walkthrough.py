"""Build matching HTML walkthroughs and executable P0 notebooks."""
from pathlib import Path
import html
import json
import sys
import textwrap
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from case_tools import load_case

def code(s):return textwrap.dedent(s).strip()+'\n'

COMMON=r'''<p>P0是一座長 \(L=30\,\mathrm{m}\)、寬 \(W=0.46\,\mathrm{m}\) 的矩形渠道。水由左向右流，\(x=0\) 是入口，\(x=30\) 是出口；上游陡坡在 \(x=11\) 至 \(13\,\mathrm{m}\) 平滑變成緩坡。固定流量與尾水後，觀察水流由淺而快變成深而慢的位置。</p>
<p>SS是Standard-step method（標準步法）；SV是Saint-Venant（聖維南淺水方程）；B是本套件的定常壓力近似Boussinesq型模型。HEC-RAS是Hydrologic Engineering Center's River Analysis System，本教學使用6.6的一維定常混合流計算。第一組使用SS／SV／B；第二組使用SS／HEC-RAS。</p>
\[\eta(x)=z_b(x)+h(x),\qquad q=\frac{Q}{W},\qquad \mathrm{Fr}=\frac{q}{\sqrt{g h^3}}.\]
<p>\(\eta\) 是水面高程、\(z_b\) 是渠底高程、\(h\) 是當地水深，皆以m為單位；\(Q\) 是總流量（m³/s）、\(q\) 是單位寬流量（m²/s），\(\mathrm{Fr}\) 是福祿數。所有水面比較圖畫 \(\eta\)；摘要中的峰高則是水深 \(h\) 的峰值。</p>
<table><tr><th>設定</th><th>P0數值與意義</th></tr>
<tr><td>總流量／單位寬流量</td><td>Q=0.05413786 m³/s；q=0.117691 m²/s</td></tr>
<tr><td>上、下游坡度</td><td>S1=0.008682536356512494；S2=0.0007079080998610611，都是小數坡度</td></tr>
<tr><td>粗糙係數與局部損失</td><td>Manning n=0.008；Cc=Ce=0</td></tr>
<tr><td>入口</td><td>依S1算正常水深，hin≈0.07067283 m；Fr≈2</td></tr>
<tr><td>出口</td><td>固定hout=0.1676558423973493 m；床高zout=0，故出口水面高程與水深數值相同</td></tr>
<tr><td>臨界水深</td><td>hc≈0.11218613 m；入口小於hc，出口大於hc</td></tr></table>
<p>完整的變床定義與方程在<a href="problem.html">問題設定</a>與<a href="methods.html">方法講義</a>。本次先重現原P0；不要直接改動cases/P0.json。</p>'''

START_A=r'''<p>先依<a href="start.html#setup">安裝頁</a>在原GC1991的WSL／Ubuntu裝好坡度套件。macOS／WSL的終端機進入解壓縮的slope-lab資料夾，執行 <code>bash start_lab.sh p0_group_a.ipynb</code>。Windows第一組的編譯與執行都在WSL／Ubuntu內進行。不要把下面的Python程式貼進終端機。</p>
<p>在Jupyter左側雙擊p0_group_a.ipynb；右上角核心選Slope Channel Lab。藍框中的說明不用執行；灰色程式格按Shift+Enter執行。看到 <code>[*]</code> 表示仍在計算，完成後會變為數字。請逐格等候，第一次不要使用Run All。</p>
<p>按Ctrl+S儲存Notebook。終端機保持開啟。計算時間依電腦而異，SV／B可能需數十秒至數分鐘；沒有新訊息時，先看核心是否仍忙碌，不要重複按執行。</p>'''

START_B=r'''<p>已完成GC1991的同學，先依<a href="start.html#setup">坡度套件安裝頁</a>在原WSL／Ubuntu裝好新版。兩組都沿用Ubuntu的Python；不需另外安裝Windows Python。</p>
<p><strong>在Ubuntu終端機</strong>進入slope-lab資料夾後執行：</p>
<pre>bash start_lab.sh p0_group_b.ipynb</pre>
<p>將本次完整token網址貼到Windows瀏覽器。Notebook核心選Slope Channel Lab；逐格按Shift+Enter，等[*]變為數字再繼續，Ctrl+S儲存。HEC-RAS 6.6仍在Windows執行，檔案來回複製依<a href="start.html#exchange">交換步驟</a>。</p>
<div class="box note">本示範Python部分已在製作環境執行；新版WSL與HEC-RAS 6.6實機驗收尚待完成。HEC欄位不預填結果。macOS及第二組Windows原生Python是<a href="start.html#alternatives">替代流程</a>。</div>'''

def steps_a():
    return [
('1. 建立自己的P0工作資料夾',START_A+r'''<p>只改學生代號，例如A1。這格會建立不重複的工作資料夾並印出完整位置。以下所有圖與表都放在該資料夾；重跑本格會建立新資料夾，後續格也要重新依序執行。</p>''',code('''
from pathlib import Path
import json, csv, uuid
import numpy as np
import lab
from postprocess import plot_compare
from demo_support import read_json, save_json, save_rows, show_table, result_rows
from IPython.display import display, Image
assert Path("cases/P0.json").is_file(), "請從 slope-lab 根目錄開啟 Notebook"
STUDENT_ID = "A1"
CASE_ID = "P0"
work = Path("runs") / ("P0_A_" + uuid.uuid4().hex[:8])
work.mkdir(parents=True, exist_ok=False)
print("本次工作資料夾：", work.resolve())
''')),
('2. 讀取物理參數，另外設定數值解析度',r'''<p>下格的case是「物理問題」，numerics是「如何計算」。P0的入口水深會由流量、寬度、粗糙係數及上游坡度自動求出，不需要另手算後輸入。核對印出的hin、hout與Fr_in。</p>
<p>SS用0.025 m斷面；SV用512個單元；B用1024個區間。這是一輪入門重現，不是三模式同網格精度比較。CFL是控制時間步大小的Courant–Friedrichs–Lewy參數；B中的lambda控制數值耗散，kappa是額外濾波的係數，均保持原值。</p>''',code('''
case = lab.load_case(CASE_ID)
numerics = dict(ss_dx=0.025, sv_N=512, b_N=1024,
                sv_CFL=0.4, b_CFL=0.1, lam=1.0, kappa=0.03,
                end=300.0, mean_start=200.0, initial="uniform")
keys = ["id", "length_m", "width_m", "Q_m3s", "q_m2s",
        "S1", "S2", "n", "hin_m", "hout_m", "yc_m", "Fr_in", "Fr_out"]
show_table([{"parameter": k, "value": case[k]} for k in keys])
save_json(work / "input.json", dict(student=STUDENT_ID, case=case, numerics=numerics))
''')),
('3. 先算標準步法，找到參考水躍',r'''<p>執行下格只需Python。先追蹤上游超臨界分支與下游次臨界分支，再用比力相等決定跳接：</p>
\[M(h)=\frac{h^2}{2}+\frac{q^2}{gh},\qquad M(h_1)=M(h_2).\]
<p>應得到 \(x_J\approx12.160061\,\mathrm{m}\)、\(h_1\approx0.07138275\,\mathrm{m}\)、\(h_2\approx0.16638210\,\mathrm{m}\)。若沒有成功狀態，先不要往下算SV或B。</p>''',code('''
ss_run = lab.run_method(case, "ss", dx=numerics["ss_dx"], output=work / "runs")
ss_jump = read_json(ss_run / "summary.json")["checks"]["jump"]
show_table([{k: ss_jump[k] for k in ["x_m", "y1_m", "y2_m"]}])
''')),
('4. 執行聖維南淺水方程',r'''<p>這一步需要安裝時建立的Basilisk編譯工具。<code>lab.build()</code>核對並準備執行程式。<code>uniform</code>表示起始時全渠先採入口水深，兩端邊界仍依P0固定。積分到物理時間300 s，輸出200–300 s的平均水面。</p>
<p>完成訊息中的「integrity passed」表示數值完整性與收支檢查通過；不等於水面已完全不隨時間變動。此P0粗網格的嚴格定常篩檢預期仍為False。</p>''',code('''
lab.build()
sv_run = lab.run_method(case, "sv", N=numerics["sv_N"],
                       CFL=numerics["sv_CFL"], initial=numerics["initial"],
                       end=numerics["end"], mean_start=numerics["mean_start"],
                       output=work / "runs")
sv_meta = read_json(sv_run / "metadata.json")
print("執行狀態：", sv_meta["status"])
print("嚴格定常篩檢：", sv_meta["steady_screen"])
''')),
('5. 執行Boussinesq型定常壓力近似模型',r'''<p>保持B=1（啟用非靜水壓修正）、lambda=1與kappa=0.03。此程式先以粗網格啟動，再逐層搜尋定常離散解，最後短時間續算核對。它不會從任意初場直接完成1024格的300 s完整物理演變。</p>
<p>因此B的續算時間是鬆弛時間；它與SV的物理300 s不是同一種時間。這一格通過也不代表波峰、波長已通過網格檢查。</p>''',code('''
b_run = lab.run_method(case, "b", N=numerics["b_N"], CFL=numerics["b_CFL"],
                      lam=numerics["lam"], B=1, kappa=numerics["kappa"],
                      initial=numerics["initial"], continuation=0.1,
                      output=work / "runs")
run_paths = {"SS": ss_run, "SV": sv_run, "B": b_run}
save_json(work / "paths.json", {name: str(p) for name, p in run_paths.items()})
print("三模式資料夾已記錄在", work / "paths.json")
''')),
('6. 疊繪完整渠道與水躍局部水面',r'''<p>程式讀各次profile.csv中的x_m與eta_m，統一畫 \(\eta=z_b+h\)，不把三條曲線水平平移對齊。左圖檢查整段渠道及邊界；右圖看水躍附近與波尾。兩張圖使用相同的物理坐標。</p>
<p>SS同一個x位置有兩個水深，故跳接接近垂直；SV的有限厚度受網格與數值通量影響；B可能有一串波峰。這些差異不能直接稱為實驗誤差。PNG適合報告，PDF適合放大列印。</p>''',code('''
figure = plot_compare(list(run_paths.values()), work / "figures")
display(Image(filename=str(figure)))
print("已存圖：", figure, "以及 comparison.pdf")
''')),
('7. 讀取位置、水深與波動指標',r'''<p>SS_xJ_m只在SS列填其動量跳接位置；SV與B用唯一50%上穿點x50_unique_m。兩者的定義不同。upstream_h_m與downstream_h_m是在固定外側區間的平均水深，不是入口／出口值，也不是直接取波峰。</p>
\[h_{50}=h_{1,\mathrm{SS}}+0.5(h_{2,\mathrm{SS}}-h_{1,\mathrm{SS}}).\]
<p>N/A表示無法唯一決定或該方法不提取此量，不是0。B的peak_h_m是第一個符合條件的水深峰值；tail_wavelength_m是第二個峰起的相鄰峰距中位數；tail_efold_m只有足夠且依序衰減的峰谷差才有定義。</p>''',code('''
rows = result_rows(run_paths)
show_table(rows)
save_rows(work / "metrics.csv", rows)
s = read_json(b_run / "summary.json")
print("B的全部10%、50%、90%上穿位置：", s["all_upcrossings_m"])
show_table(s["extrema"])
save_rows(work / "B_peaks.csv", s["extrema"])
sv_checks = read_json(sv_run / "summary.json")["checks"]
print("SV前後半平均最大差 (mm)：", 1000 * sv_checks["block_depth_change_m"])
print("SV最大時間標準差 (mm)：", 1000 * sv_checks["max_depth_sd_m"])
''')),
('8. 核對是否重現既有P0，而非只看曲線相似',r'''<p>下格逐點比較本次水深與隨包附上的凍結參考資料，不重新平移或縮放曲線。應三列passed皆為True。它驗證你使用了相同程式設定；參考本身不是實驗真值。</p>
<p>若SV定常篩檢為False、但本格重現通過，兩者不矛盾：前者問「時間變化夠小嗎」，後者問「是否重算出原結果」。</p>''',code('''
checks = []
for method, folder, refname, tol in [
    ("SS", ss_run, "ss_P0_dx0025.csv", 1e-8),
    ("SV", sv_run, "sv_N512_T300.dat", 2e-4),
    ("B", b_run, "b_N1024.dat", 1e-5)]:
    a = np.genfromtxt(folder / "profile.csv", delimiter=",", names=True,
                      dtype=None, encoding="utf-8")
    if method == "SS":
        ref = np.genfromtxt(Path("reference") / refname, delimiter=",", names=True)
        xx, hh = ref["x_m"], ref["h_m"]
    else:
        ref = np.loadtxt(Path("reference") / refname)
        xx, hh = ref[:, 0], ref[:, 1]
    assert len(xx) == len(a) and np.max(abs(xx-a["x_m"])) < 1e-8
    error = float(np.max(abs(hh-a["h_m"])))
    checks.append(dict(method=method, max_depth_difference_m=error,
                       tolerance_m=tol, passed=error <= tol))
show_table(checks)
save_json(work / "reproduction.json", checks)
assert all(c["passed"] for c in checks), "保留結果並核對設定，不要調大門檻"
''')),
('9. 保存並撰寫第一段判讀',r'''<ol><li>記錄SS跳接約12.16 m，說明坡度轉換區是11–13 m。</li><li>從metrics.csv抄入SV與B的唯一x50及外側水深，不混用三種位置定義。</li><li>描述B是否出現波峰，附峰高與峰距；本次只有一層B網格，不可寫「波形已收斂」。</li><li>寫出SV定常篩檢結果、與凍結資料的重現差異，解釋兩項檢查不同。</li></ol>
<p>可採用句型：「在相同P0物理條件下，SS得到……；SV的200–300 s平均水面……；B的離散定常解……。三者對位置／外側水深呈現……，但本次尚未檢查……。」請以自己的數值填空。</p>
<p>保留整個work資料夾、已儲存的p0_group_a.ipynb、輸入、三次原始run、metrics.csv、B_peaks.csv、reproduction.json及兩種格式的圖。之後依<a href="group_a.html">第一組正式任務</a>進行1024／2048與控制試算。本次不自動啟動那些額外計算。</p>''',None)]

def steps_b():
    return [
('1. 開啟第二組Notebook並建立工作資料夾',START_B,code('''
from pathlib import Path
import json, uuid, shutil, csv
import numpy as np
import lab
from hec_tools import export_project, compare_export
from postprocess import plot_compare
from demo_support import read_json, save_json, save_rows, show_table
from IPython.display import display, Image
assert Path("cases/P0.json").is_file(), "請從 slope-lab 根目錄開啟 Notebook"
STUDENT_ID = "B1"
CASE_ID = "P0"
work = Path("runs") / ("P0_B_" + uuid.uuid4().hex[:8])
work.mkdir(parents=True, exist_ok=False)
print("請記下此資料夾，HEC與Python都使用這一次：", work.resolve())
''')),
('2. 設定P0與三種斷面間距',r'''<p>斷面是沿渠道取樣水位與幾何的位置。這一輪只改斷面間距，流量、床坡、粗糙係數與邊界皆不變。0.5、0.25、0.125 m分別有61、121、241個斷面，因為包含兩端。</p>
<p>入口仍由實際S1計算正常水深。HEC使用總流量Q，不能填0.117691這個單位寬流量。</p>''',code('''
case = lab.load_case(CASE_ID)
spacings = [0.5, 0.25, 0.125]
show_table([{"parameter": k, "value": case[k]} for k in
            ["length_m", "width_m", "Q_m3s", "S1", "S2", "n", "hin_m", "hout_m"]])
save_json(work / "input.json", dict(student=STUDENT_ID, case=case, spacings_m=spacings))
''')),
('3. 先跑三次Python標準步法',r'''<p>下面會依序執行三次SS，保存三個獨立資料夾並疊圖。列表的xJ_m取自每一次實際解的動量跳接，不使用共用細網格參考位置。越細的斷面越接近12.16 m；稍後HEC也要逐一做相同間距。</p>''',code('''
ss_runs = [lab.run_method(case, "ss", dx=dx, output=work / "runs") for dx in spacings]
ss_rows = []
for dx, folder in zip(spacings, ss_runs):
    jump = read_json(folder / "summary.json")["checks"]["jump"]
    ss_rows.append(dict(dx_m=dx, sections=int(round(30/dx))+1,
                        xJ_m=jump["x_m"], h1_m=jump["y1_m"], h2_m=jump["y2_m"]))
show_table(ss_rows)
save_rows(work / "SS_spacing.csv", ss_rows)
figure = plot_compare(ss_runs, work / "SS_figures")
display(Image(filename=str(figure)))
''')),
('4. 產生HEC專案與真正配對的Python基準',r'''<p>這格建立三份原生專案；不要另用手打數值重建P0。每份包含.prj專案、.g01幾何、.f01流量、.p01計畫，必須整個資料夾一起保留。</p>
<p>HEC文字欄位會捨入流量／床高，因此paired_ss.csv採用「實際寫入HEC檔案的值」重算Python水面。它仍是Python輸出；不可改名為HEC結果。下表的SS_xJ_m就是後續應比較的配對跳接。</p>''',code('''
hec_folder = export_project(case, work / "HEC_projects")
project_rows = []
for dx in spacings:
    project = hec_folder / ("dx" + str(dx).replace(".", "p"))
    e = read_json(project / "expected.json")
    project_rows.append(dict(dx_m=dx, sections=e["section_count"],
                            Q_written_m3_s=e["Q_written_m3s"],
                            SS_xJ_m=e["SS_jump_m"]))
show_table(project_rows)
save_rows(work / "paired_SS_spacing.csv", project_rows)
(work / "HEC_exports").mkdir(exist_ok=True)
save_json(work / "paths.json", dict(hec_folder=str(hec_folder),
                                   ss_runs=[str(p) for p in ss_runs]))
print("第一個要開的檔案：", hec_folder / "dx0p5" / "P0.prj")
''')),
('5. 在HEC-RAS 6.6開檔，核對幾何',r'''<p><strong>從這一步切換到Windows的HEC-RAS，不在Notebook執行。</strong>保持Notebook開著。依<a href="start.html#exchange">安裝頁第5步</a>，把本次整個HEC_projects複製到Windows本機，再在Windows複本計算。記下P0_B_八碼，不要只傳.prj。</p>
<ol><li>啟動HEC-RAS 6.6，用Help → About記錄版本。主視窗File → Open Project，選Windows複本中的HEC_projects\\dx0p5\\P0.prj；Ubuntu印出的路徑用來找到來源資料夾。</li><li>選Options → Unit System，確認SI（Metric）。開啟Edit → Geometric Data，再進入Cross Section。</li><li>河道SlopeChannel、河段Main。River Station從入口30遞減至出口0。本教材的下游坐標為 \(x=30-\mathrm{River\ Station}\)。</li><li>在入口、轉坡段、出口各看一個斷面。Station/Elevation應是四個點：\((0,z_b+2),(0,z_b),(0.46,z_b),(0.46,z_b+2)\)。它們構成垂直側壁；兩個底點須同高。</li><li>左右Bank Stations為0與0.46 m；Manning n=0.008；Contraction與Expansion均為0。相鄰斷面通道長度為0.5 m（最下游沒有下一段）。</li></ol>
<p>保存幾何與單位畫面。若6.6無法讀取某個檔案，先停止並保存訊息交助教，不要以猜測欄位值繼續。所有核對值也在各子資料夾的sections.csv與expected.json。</p>''',None),
('6. 設定流量、兩端邊界與Mixed求解',r'''<ol><li>Edit → Steady Flow Data。確認只有一個P0流量剖面；入口總流量為 \(0.0541379\,\mathrm{m^3/s}\)（HEC文字格式捨入後）。</li><li>點Reach Boundary Conditions。上游選Normal Depth，填斜率0.008682536356512494；下游選Known W.S.，填0.1676558423973493 m。這是水面高程，因本案出口床高為0才與尾水深度相等。</li><li>保存流量。主視窗Run → Steady Flow Analysis，核對幾何與流量均為本次P0，Flow Regime選Mixed（混合流）。</li><li>Options → Friction Slope Methods選Average Friction Slope（摩阻坡度算術平均）。Options → Set Calculation Tolerances核對：Standard Step Tol與Critical Tol均為0.00001 m、Max Error Tol=0.0001 m、最多100次、Flow Tol Ratio=0.000001。</li><li>按Compute。等完成後保存計算訊息／警告，並到View → Water Surface Profiles看沿程水面。不要把「執行完成」當成無警告或已驗證。</li></ol>
<p>預期入口Fr約2、出口Fr約0.547，水躍大致在x=12 m附近。具體HEC結果必須以你的實際運算為準；遇到critical depth替代或警告要保留。</p>
<p class="small">Mixed流態與雙邊界的用途可查<a href="https://www.hec.usace.army.mil/software/hec-ras/documentation/HEC-RAS_Hydraulic_Reference_Manual_v6.6.pdf">USACE 6.6技術手冊</a>。圖形介面名稱及可選項以6.6實機為準，更多設定說明見<a href="hec66.html">本包6.6核對頁</a>。</p>''',None),
('7. 匯出真實結果，整理四欄CSV',r'''<ol><li>主視窗View → Profile Summary Table。只選本次P0計畫、P0剖面及SlopeChannel/Main河段，顯示全部斷面。</li><li>使用標準表或自訂表，包含River Sta、W.S. Elev、Froude # Chl及Q Total。Options內確認Metric；調整顯示小數位，水面高程至少6位、流量至少7位、Fr至少4位。</li><li>用表格視窗File → Copy to Clipboard複製，貼到試算表並先保存原始表。不要把畫面上四捨五入成0.05的Q當成原始流量。</li><li>另建四欄，依序命名 <code>river_station,water_surface_m,Fr,Q_m3_s</code>。從原表複製對應的數值列，移除重複標題、單位列、其他河段／剖面。不要自行填入Python水面。</li><li>另存「CSV UTF-8（逗號分隔）」，dx0p5應有61筆資料加1列表頭，先保存到Windows本次工作資料夾的HEC_exports/P0_dx0p5.csv，再複製回Ubuntu同一次work/HEC_exports/P0_dx0p5.csv（work就是步驟1的P0_B_八碼資料夾）。</li><li>再開dx0p25/P0.prj與dx0p125/P0.prj，重做步驟5–7，分別保存P0_dx0p25.csv（121筆）及P0_dx0p125.csv（241筆）。不能只把第一份CSV換檔名。</li></ol>
<pre>river_station,water_surface_m,Fr,Q_m3_s</pre>
<p>檔案回傳請依<a href="start.html#exchange">交換步驟</a>，另保留HEC_raw與HEC_computed_windows，勿覆寫原配對輸入。</p><p>上方只有表頭，刻意沒有示範HEC數值列，以免被當成實際輸出。原始表、版本、計算訊息與整份原生專案都要一起保留。表格操作依<a href="https://www.hec.usace.army.mil/confluence/rasdocs/rasum/6.6/viewing-results/tabular-output">USACE 6.6表格章節</a>；較完整的<a href="https://www.hec.usace.army.mil/confluence/rasdocs/rasum/6.7_beta5/viewing-results/tabular-output">官方表格操作頁</a>說明了複製及小數位選項，此頁版本為6.7 beta，請在6.6實機核對名稱。</p>''',None),
('8. 回到Python檢查匯出，繪製配對水面',r'''<p>回到同一份Notebook執行下格。不需把路徑手改成教師電腦的絕對路徑：只要CSV放在本次工作資料夾即可。缺少CSV會顯示「待完成」，不會捏造HEC曲線；成功的檔案才會產生比較圖。</p>
<p>若重啟過核心，先不要重跑步驟1而忘記舊資料夾。在新增程式格讀回路徑即可：</p>
<pre>work = Path("runs/P0_B_你先前記下的八碼")
hec_folder = Path(read_json(work / "paths.json")["hec_folder"])</pre>
<p>上例需把八碼換成實際名稱；並先執行步驟1中的import行。比較器會核對斷面、流量與Fr的一致性；失敗時保留錯誤訊息，先回查來源表與單位。</p>''',code('''
hec_results = []
for key in ["dx0p5", "dx0p25", "dx0p125"]:
    source = work / "HEC_exports" / ("P0_" + key + ".csv")
    if not source.is_file():
        print("待完成真實HEC匯出：", source)
        continue
    out = work / ("compare_" + key + "_" + uuid.uuid4().hex[:8])
    result = compare_export(hec_folder / key, source, out)
    hec_results.append(result)
    display(Image(filename=str(out / "comparison.png")))
    print("比較結果與差值資料：", out)
save_json(work / "HEC_comparisons.json", hec_results)
show_table([dict(dx_m=r["dx_m"], HEC_jump_brackets_m=r["jump_brackets_m"],
                 paired_SS_xJ_m=r["SS_xJ_m"],
                 eta_RMSE_mm=1000*r["eta_RMSE_m"],
                 eta_max_difference_mm=1000*r["eta_Linf_m"]) for r in hec_results])
print("已完成的HEC間距數：", len(hec_results), "/ 3")
''')),
('9. 放大水躍區並畫水面差',r'''<p>整體水面幾乎重合時仍可能有水躍位置差。下格讀取比較器剛產生的comparison.csv，左圖看x=10–15 m，右圖畫 \(\eta_{\mathrm{HEC}}-\eta_{\mathrm{SS}}\)（mm）。它只處理本次已完成的真實HEC資料。</p>
<p>HEC在相鄰斷面間由Fr&gt;1轉為Fr&lt;1時，只能確定跳接落在一個區間。不要用連線的斜度估計物理水躍長度；也不要把區間中點當成精確跳接點。</p>''',code('''
import matplotlib.pyplot as plt
# 每一間距只取本次最新的比較資料夾。
for key in ["dx0p5", "dx0p25", "dx0p125"]:
    candidates = [p for p in work.glob("compare_" + key + "_*")
                  if (p / "comparison.csv").is_file()]
    if not candidates:
        continue
    folder = max(candidates, key=lambda p: p.stat().st_mtime_ns)
    a = np.genfromtxt(folder / "comparison.csv", delimiter=",", names=True)
    fig, ax = plt.subplots(1, 2, figsize=(11, 4), layout="constrained")
    ax[0].plot(a["x_m"], a["eta_ss_m"], label="Python SS")
    ax[0].plot(a["x_m"], a["eta_hec_m"], "o-", ms=3, label="HEC-RAS 6.6")
    ax[0].set(xlim=(10, 15), xlabel="x (m)", ylabel="Water-surface elevation (m)")
    ax[0].legend()
    ax[1].plot(a["x_m"], 1000*a["difference_m"])
    ax[1].axhline(0, color="gray", lw=0.8)
    ax[1].set(xlabel="x (m)", ylabel="HEC minus SS (mm)")
    for panel in ax: panel.grid(alpha=0.2)
    fig.savefig(folder / "detail_and_difference.png", dpi=180)
    fig.savefig(folder / "detail_and_difference.pdf")
    display(fig)
    plt.close(fig)
''')),
('10. 判讀與繳交',r'''<p>逐一列出三種間距、配對SS的xJ、HEC全部跳接區間、全渠道水面RMSE與最大差，以及警告。沒有上游超臨界轉下游次臨界的區間時記錄N/A並檢查；多個區間時全部保留。</p>
\[\mathrm{RMSE}_{\eta}=\sqrt{\frac{1}{m}\sum_{i=1}^{m}(\eta_{\mathrm{HEC},i}-\eta_{\mathrm{SS},i})^2}.\]
<p>m是配對斷面數。這是兩模式的差異，不是對實驗的誤差。跳接稍微位移時，局部最大差可能很大；需連同區間判讀，不能僅靠單一RMSE下結論。</p>
<p>判讀句型：「在0.5、0.25、0.125 m斷面下，HEC跳接分別位於……，配對SS位置為……。加密後區間／水面差呈現……。計算出現／未出現……警告，因此本比較支持……，尚不能支持真實水躍長度。」沒有實際HEC輸出時，最後一段明寫待實機完成。</p>
<p>繳交work整個資料夾、儲存的p0_group_b.ipynb、三個HEC原生專案與輸出、原始匯出表、整理後CSV、比較圖與書面判讀。確認HEC_comparisons.json有3筆真正的比較，不能以空陣列視為完成。</p>''',None)]

def notebook(name, title, steps):
    cells=[dict(cell_type='markdown',id='intro',metadata={},source=('# '+title+'\n\n'+COMMON.replace(r'\[','$$').replace(r'\]','$$').replace(r'\(','$').replace(r'\)','$')).splitlines(True))]
    for i,(title,body,source) in enumerate(steps,1):
        body=body.replace(r'\[','$$').replace(r'\]','$$').replace(r'\(','$').replace(r'\)','$')
        # Local guides are in docs when the notebook lives in the kit root.
        import re
        body=re.sub(r'href="([a-z0-9_]+\.html(?:#[^"]*)?)"',r'href="docs/\1"',body)
        cells.append(dict(cell_type='markdown',id=f'text-{i}',metadata={},source=('## '+title+'\n\n'+body).splitlines(True)))
        if source:
            cells.append(dict(cell_type='code',id=f'code-{i}',execution_count=None,metadata={},outputs=[],source=source.splitlines(True)))
    # HTML guides live in docs/, while notebooks live at the kit root.
    for cell in cells:
        if cell['cell_type'] == 'markdown':
            cell['source'] = [re.sub(r'href="([a-z_]+\.html(?:#[^"]*)?)"', r'href="docs/\1"', line) for line in cell['source']]
    data=dict(cells=cells,metadata=dict(kernelspec=dict(display_name='Slope Channel Lab',language='python',name='slope-lab'),language_info=dict(name='python',version='3.12')),nbformat=4,nbformat_minor=5)
    (ROOT/name).write_text(json.dumps(data,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')

def build(write,table):
    pages={}
    for group,steps,title in [('a',steps_a(),'P0第一組完整示範：標準步法／聖維南／Boussinesq型模型'),
                              ('b',steps_b(),'P0第二組完整示範：Python標準步法／HEC-RAS 6.6')]:
        name=f'p0_group_{group}.ipynb';notebook(name,title,steps)
        intro='<p class="lead">跟著本頁完成一輪P0：每一步都標明操作位置、應看到的結果及判讀方式。程式區塊與附帶Notebook一致。</p>'
        intro+=f'<p><a href="../{name}">Notebook檔案：{name}</a>（在Jupyter中開啟） · <a href="p0_demo.html">兩組示範入口</a></p>'
        body=intro+COMMON+'<h2>操作目錄</h2><ol>'+''.join(f'<li><a href="#step-{i}">{t}</a></li>' for i,(t,_,_) in enumerate(steps,1))+'</ol>'
        for i,(t,b,c) in enumerate(steps,1):
            body+=f'<section id="step-{i}"><h2>{t}</h2>'+b
            if c:body+='<p class="small">在Notebook執行以下整格：</p><pre><code>'+html.escape(c)+'</code></pre>'
            body+='</section>'
        evidence=ROOT/'examples/P0_demo/demo_summary.json'
        if evidence.exists():
            d=json.loads(evidence.read_text())
            if group=='a':
                body+='<h2>本次實際執行的示範結果</h2><p>以下是本教學Notebook以原P0參數重新執行的輸出；未改動既有凍結參考。學生可用來檢查量級，精確重現仍以下格逐點比對為準。</p>'
                body+=table(['模式','位置定義','位置m','上游平均h m','下游平均h m','峰h m','尾波峰距m'],[[r['method'],'SS比力跳接' if r['method']=='SS' else '唯一50%上穿',f"{(r['SS_xJ_m'] if r['method']=='SS' else r['x50_unique_m']):.6f}" if (r['SS_xJ_m'] if r['method']=='SS' else r['x50_unique_m']) is not None else 'N/A',f"{r['upstream_h_m']:.6f}",f"{r['downstream_h_m']:.6f}",'N/A' if r['peak_h_m'] is None else f"{r['peak_h_m']:.6f}",'N/A' if r['tail_wavelength_m'] is None else f"{r['tail_wavelength_m']:.6f}"] for r in d['A_metrics']])
                body+='<div class="example"><h3>示範判讀</h3><p>SS在坡度轉換段內跳接，位置約12.160 m。SV與B的唯一50%上穿位置分別約比SS下游12 mm與49 mm；這是不同定義下的位置比較，不能直接當成誤差。三模式外側平均水深都接近上游0.0707 m、下游0.1677 m，顯示大尺度水深相近。</p><p>B第一個水深峰約0.17988 m，三個可辨峰的峰谷差約14.96、0.643、0.0267 mm，這一次計算沿下游衰減。但只有3個可辨峰，不足套件要求的至少4峰，因此衰減長度為N/A；不能從此單一網格宣布波尾已收斂。尾波峰距約0.518 m，此值本次僅來自第二與第三峰。</p><p>SV前後半平均最大差約2.102 mm、最大時間標準差約1.147 mm，因此嚴格定常篩檢為False。三方法與凍結參考的最大水深差分別約0、10⁻¹²、9.33×10⁻¹⁰ m，三項重現檢查仍通過。</p><p>圖上B最高水面高程會高於0.17988 m，因為圖畫的是η，而峰值表列的是h；當地渠底高程也要加上。</p></div>'
                body+='<figure><img src="../examples/P0_demo/A_comparison.png" alt="P0三模式完整與局部水面高程"><figcaption>SS為定常跳接；SV為200–300 s平均；B為1024區間離散定常解短續算端點。不同曲線不是同一瞬間的實驗水面。</figcaption></figure>'
            else:
                body+='<h2>本次Python實算與HEC待填欄位</h2>'
                body+=table(['間距m','斷面數','原P0 SS xJ m','配對HEC輸入SS xJ m','HEC區間'],[[r['dx_m'],r['sections'],f"{r['xJ_m']:.6f}",f"{p['SS_xJ_m']:.6f}",'待6.6實機計算'] for r,p in zip(d['B_SS'],d['B_paired'])])
                body+='<div class="example"><h3>示範判讀</h3><p>Python原P0的跳接由12.180342、12.165267變成12.161187 m；相鄰兩次加密的位移約15.08 mm與4.08 mm。位移縮小支持位置開始穩定的趨勢，但三點本身不等於已算出嚴格誤差界限。</p><p>配對HEC文字輸入的Python位置只相差約0.01 mm，仍應使用配對值比較。HEC欄位目前留白；實機完成後先看SS位置是否落在HEC超臨界轉次臨界的斷面區間，再比較水面差與警告。</p></div>'
                body+='<figure><img src="../examples/P0_demo/B_SS_comparison.png" alt="P0三種斷面間距Python標準步法水面"><figcaption>此圖三條皆為Python標準步法，沒有HEC曲線。HEC比較圖會在你提供真實CSV後產生。</figcaption></figure>'
            body+='<p><a href="../examples/P0_demo/demo_summary.json">完整示範數值與重現檢查</a> · <a href="../examples/P0_demo/README.org">資料來源與執行範圍</a></p>'
        body+='<h2>第一次操作常見問題</h2><table><tr><th>現象</th><th>下一步</th></tr><tr><td>No module named lab／找不到cases/P0.json</td><td>Notebook不在套件根目錄，或核心選錯；回安裝頁核對。</td></tr><tr><td>NameError，例如work未定義</td><td>核心重啟或跳格；從imports與工作路徑設定恢復，計算格不要無意重跑。</td></tr><tr><td>畫不出圖</td><td>先看前一計算格是否成功；不要拿failed狀態的資料畫成功圖。</td></tr><tr><td>圖與講義有差</td><td>核對P0、uniform、N、CFL、lambda及平均時間，再看逐點比較；勿用改n讓圖相似。</td></tr><tr><td>HEC流量／Fr檢查失敗</td><td>核對SI單位、輸出小數位、是否取錯Q或水深欄；不要放寬檢查值。</td></tr></table>'
        pages[group]=body;write(f'p0_group_{group}.html',title,body)
    landing='<p class="lead">兩條可以從頭跟做的P0流程：選自己的組別，依序完成設定、計算、繪圖與判讀。</p><p><a href="p0_group_a.html">第一組：SS／SV／B，9個步驟</a><br><a href="p0_group_b.html">第二組：SS／HEC-RAS 6.6，10個步驟</a></p><p>每條流程各附一份Notebook，與HTML程式格一致。P0參數固定、方程使用LaTeX，結果與舊研究資料分開保存。</p><p>第一組有重新計算的三模式參考圖與指標；第二組有三種斷面的Python參考圖、HEC逐項設定及真實匯出後的比較程式。HEC尚待Windows實機驗收，不提供代填結果。</p><p>已完成GC1991者，先依<a href="start.html">既有Windows／WSL接續安裝</a>加裝坡度套件，再開所屬組別P0。整體理論見<a href="handbook.html">獨立講義</a>。</p>'
    write('p0_demo.html','P0完整操作示範：從參數到成果',landing)
