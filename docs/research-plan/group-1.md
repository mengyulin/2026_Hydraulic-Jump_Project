# 第一組：水躍之深度平均模擬

**A1–A5 · 五人各負責一個物理因子 · 整合稿 2026-10-22**

本組比較 Python 標準步法（SS）、聖維南淺水方程（SV）與本套件的定常壓力近似 Boussinesq 型模型（B）。先跟做 P0，再研究同一渠道改變一個因子後，水躍位置、水深與波動如何改變。

本頁只列研究任務與分工。完整的[問題與參數](../../slope-lab/docs/problem.html)、[方程及符號](../../slope-lab/docs/methods.html)、[逐步計算](../../slope-lab/docs/p0_group_a.html)分別在教材中說明。

<a id="contents"></a>
## 本頁導覽

- [先完成P0](#start)
- [五人分工](#work)
- [每人需要完成的計算](#objectives)
- [成果與跨組交換](#outcomes)

<a id="start"></a>
## 先完成P0

1. [下載v1.3教學包](../../downloads/slope-lab-v1.3.zip)，依[接續安裝頁](../../slope-lab/docs/start.html)沿用GC1991的Windows／WSL，另建坡度套件環境。
2. 跟做[第一組P0示範](../../slope-lab/docs/p0_group_a.html)，逐格執行 <code>p0_group_a.ipynb</code>。
3. 交出完整／局部水面圖、指標表與逐點重現檢查。說清楚SS跳接、SV平均水面與B離散定常解的差別。
4. P0跑通後，再使用原 <code>student_lab.ipynb</code> 與自己的操作單進行低、高水準。

P0的數值重現已完成；SV粗網格不是嚴格靜止解，B波形也尚未證明網格獨立。[已完成檢查與限制](../../slope-lab/docs/verification.html)集中在同一頁。GN與剪切淺水方程不列入本次必做範圍。

<a id="work"></a>
## 五人分工

| 同學 | 研究因子 | 個人案例 | 操作單／跨組夥伴 |
|---|---|---|---|
| A1 | 上游坡度與入口福祿數 | P0、P1L、P1H | [A1操作單](../../slope-lab/docs/assignments/A1.html)；對接B1 |
| A2 | 出口尾水 | P0、P2L、P2H | [A2操作單](../../slope-lab/docs/assignments/A2.html)；對接B2 |
| A3 | 坡度轉換長度 | P0、P3L、P3H | [A3操作單](../../slope-lab/docs/assignments/A3.html)；對接B3 |
| A4 | 下游坡度 | P0、P4L、P4H | [A4操作單](../../slope-lab/docs/assignments/A4.html)；對接B4 |
| A5 | Manning粗糙係數 | P0、P5L、P5H | [A5操作單](../../slope-lab/docs/assignments/A5.html)；對接B5 |

各因子的精確數值、哪些條件連動及保持不變的設定，以[案例設計表](../../slope-lab/docs/design.html)與隨包JSON為準，不在此另複製一份數字表。

<a id="objectives"></a>
## 每人需要完成的計算

- 三個物理條件使用同一套輸入。標準步法用三種斷面間距；SV／B先以512檢查，再依操作單完成1024／2048主要比較。
- 選定一個個人變體，完成時間步減半、B off與固定數值耗散尺度的指定對照。具體命令、參數及順序見[個人案例計算流程](../../slope-lab/docs/group_a.html)。
- 保持物理粗糙度與數值耗散的意義分開。不要改Manning n讓波峰消失，或把平滑的曲線直接視為較準。
- 保留失敗、沒有唯一交點與峰數不足的結果。用證據說明「位置較穩定但波形仍改變」也可以是合理成果。

B模式的波動是研究題目，不要求每位學生都把它消除或完成很嚴格的收斂證明；但不能把單一網格的峰高當作已驗證的物理預測。

<a id="outcomes"></a>
## 成果與跨組交換

每人交付：三條件的輸入表、三模式完整／局部水面圖、位置與水深趨勢、波動指標、解析度與指定控制對照，以及可重跑的資料。

與[第二組](group-2.md)同編號夥伴交換P0及兩個變體的數值剖面，而非只交換圖片。位置定義、資料欄位與週次見[共同比對](comparison.md)；[正式繳交格式](../../slope-lab/docs/submission.html)是全組共用標準。
