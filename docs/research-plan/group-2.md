# 第二組：水躍之工程水理分析

**B1–B5 · 五人各負責一個物理因子 · 整合稿 2026-10-22**

本組比較 Python 標準步法與 HEC-RAS 6.6 的一維定常混合流。給定同一渠道、流量、粗糙度與尾水，研究水面線與水躍所在區間是否相近，以及差異如何隨斷面間距改變。

本頁只列研究任務與分工。[問題與參數](../../slope-lab/docs/problem.html)、[標準步法原理](../../slope-lab/docs/methods.html#method-ss)與[HEC逐步操作](../../slope-lab/docs/p0_group_b.html)集中在教材。B1–B5是學生代號；本組不計算Boussinesq型B模型。

<a id="contents"></a>
## 本頁導覽

- [先完成P0](#start)
- [五人分工](#work)
- [每人需要完成的比較](#objectives)
- [成果與跨組交換](#outcomes)

<a id="start"></a>
## 先完成P0

1. [下載v1.3教學包](../../downloads/slope-lab-v1.3.zip)，依[GC1991接續安裝](../../slope-lab/docs/start.html)沿用原WSL／Ubuntu執行Python；HEC-RAS 6.6在Windows運作。
2. 跟做[第二組P0示範](../../slope-lab/docs/p0_group_b.html)，用 <code>p0_group_b.ipynb</code> 計算三種斷面間距的Python水面並產生HEC專案。
3. 依[檔案交換步驟](../../slope-lab/docs/start.html#exchange)複製完整專案到Windows，再在HEC-RAS 6.6核對幾何、流量、邊界、Mixed及摩阻平均方式後Compute，保存版本與警告。
4. 匯出真正的HEC結果，回到Notebook完成配對圖、差值圖與水躍區間表。缺少HEC匯出時保留「待完成」。

三份P0原生輸入與靜態檢查已備妥，**HEC 6.6實機開檔／計算仍待教師或助教預試**。這與Python數值重現分開；<code>paired_ss.csv</code> 是Python基準，不能當成HEC結果。

<a id="work"></a>
## 五人分工

| 同學 | 研究因子 | 個人案例 | 操作單／跨組夥伴 |
|---|---|---|---|
| B1 | 上游坡度與入口福祿數 | P0、P1L、P1H | [B1操作單](../../slope-lab/docs/assignments/B1.html)；對接A1 |
| B2 | 出口尾水 | P0、P2L、P2H | [B2操作單](../../slope-lab/docs/assignments/B2.html)；對接A2 |
| B3 | 坡度轉換長度 | P0、P3L、P3H | [B3操作單](../../slope-lab/docs/assignments/B3.html)；對接A3 |
| B4 | 下游坡度 | P0、P4L、P4H | [B4操作單](../../slope-lab/docs/assignments/B4.html)；對接A4 |
| B5 | Manning粗糙係數 | P0、P5L、P5H | [B5操作單](../../slope-lab/docs/assignments/B5.html)；對接A5 |

精確設定以[案例設計表](../../slope-lab/docs/design.html)與隨包JSON為準。改一個因子時，先檢查哪些邊界或正常水深會連動，不手改一組看似獨立的數字。

<a id="objectives"></a>
## 每人需要完成的比較

- P0與低、高兩個變體，各用0.5、0.25、0.125 m斷面間距做Python／HEC比較。
- 以每份HEC專案的 <code>paired_ss.csv</code> 作嚴格配對基準，因為它使用文字檔真正儲存的流量與床高。
- 記錄HEC所有超臨界轉次臨界的斷面區間；不要把區間中點當成精確跳接位置。
- 先核對輸入與設定，再研究加密。保留臨界水深替代與警告，不能先調粗糙度或尾水使曲線重合。

完成P0後，用[第二組個人案例流程](../../slope-lab/docs/group_b.html)產生新專案。每次運算保留原始輸入、HEC原生輸出與匯出表；標準步法的零長度跳接不預測實際滾流長度。

<a id="outcomes"></a>
## 成果與跨組交換

每人交付：三條件的輸入表、三種斷面間距、配對水面／差值圖、HEC水躍區間與Python比力匹配位置、警告紀錄及差異解釋。

與[第一組](group-1.md)同編號夥伴交換數值剖面，加入SV／B結果作共同分析。比對定義、資料交換及週次見[共同比對](comparison.md)；正式檔案與報告格式見[成果繳交](../../slope-lab/docs/submission.html)。
