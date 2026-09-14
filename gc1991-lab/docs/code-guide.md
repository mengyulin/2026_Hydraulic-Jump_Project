# 程式導讀

先從 Notebook 看呼叫順序，再閱讀對應水理段落。核心程式採英文註解以保留公式名稱；本頁提供中文導覽。

## 第一層：學生操作

`student_lab.ipynb` 只做四類事情：載入設定、呼叫計算、顯示誤差、畫圖。`lab.py` 是共同入口：

| 函式 | 用途 |
|---|---|
| `load_case()` | 讀取固定 Test 4 設定，每次回傳獨立副本 |
| `initial_rows()` | 以漸變流方程及 RK4 建立急流初始水面，處理 h,u 與 h,q 的差異 |
| `run_method(case, method)` | 建立獨立輸出目錄、生成輸入、編譯／執行、核對完成狀態 |
| `run_all(case)` | 依序執行三種方法 |
| `check_result()` | 與封存結果核對，避免未完成結果被當成成功 |
| `plot_compare(results)` | 讀取此次實際水面、疊合實驗、保存圖與來源 |

共同輸入為 `cases/test4.json`；不要自行編輯執行目錄內的 `config.dat` 再期待 Notebook 採用它，因為每次執行都會由 JSON 重新產生輸入。

## 第二層：Python 水理核心

閱讀 [`core/standard_step.py`](../core/standard_step.py)：

1. `energy()`、`force()`、`critical()`、`conjugate()` 對應基本水理公式。
2. `friction()` 使用完整矩形水力半徑。
3. `step()` 解相鄰斷面的能量平衡，將急流與緩流根分開。
4. `solve()` 建立兩個分支，找比力殘差換號的位置。

`h` 是水深、`q` 是單寬流量，並非總流量 Q。`wide=False` 是目前實際使用的矩形渠道形式。`critical_distance()` 是附帶的深度座標檢查工具，課堂流程沒有呼叫。

## 第三層：顯式 Saint-Venant

閱讀 [`core/sv_case.c`](../core/sv_case.c)：

- `main()` 接收物理與數值設定；`event init` 載入格心水深、流速。
- `update_checked()` 在預測與修正階段使用一致 Manning 源項。
- `advance_checked()` 保存實際邊界流量、動量與摩阻累積，並處理時間平均。
- `event observe` 檢查正水深、流速與收支；`event finish` 寫入完成水面。

[`core/sv_instrumented.h`](../core/sv_instrumented.h) 是附有原生 literate comments 的 Basilisk 標頭副本。重點是 `update_saint_venant` 內對左右外邊界面通量的設定及 `stage_qin` 等收支量。`sv-boundary.patch` 可用來確認與隨附原生標頭的差異。

教學副本移除了歷史來源中未啟用的 GN 條件區塊。原因是 qcc 在 C 預處理前就掃描 include，否則仍要求 GN 檔案。選定的 SV 方程與時間更新內容維持不變。

## 第四層：自訂求解器

閱讀 [`core/custom_solver.c`](../core/custom_solver.c)：

| 程式位置 | 水理／離散意義 |
|---|---|
| `State { h, q }` | 兩個守恆變量 |
| `weight()`、`sum_state()` | 兩端半寬控制體與全域積分 |
| `radius()`、`source()` | 水力半徑與摩阻源項 |
| `operator()` | 速度導數、B 通量、Rusanov 通量與人工輸運；同一面以相反符號供相鄰控制體使用 |
| `valid()`、`failure_dump()` | 中間階段異常即停止並保存診斷 |
| `event` 更新段 | predictor／corrector、面通量收支與時間平均 |
| `event outputs` | 輸出節點水深、q、平均值及收支 |

第一版固定 `source_mode=0`（顯式摩阻）、`strip_mode=2`（全域 Rusanov）、B=1、κ=0.03。其他分支是保留的研究程式，並非此教材已驗收的替代方案。課堂不需要逐行理解所有診斷陣列。

## 再現與實驗驗證

`reference/source_provenance.json` 記錄研究來源與 SHA-256；`vendor/basilisk-source.json` 記錄完整 Basilisk 原始碼快照。歷史研究安裝與教材快照之間有六個相依標頭不同，記錄在 `vendor/historical-comparison.json`；教材使用完整一致的快照，沒有混合標頭版本。是否重現既有結果以實際 CPU 計算核對，而非假定編譯器相同。

`tests/test_lab.py` 只做小型公式、分支、初始條件與錯誤輸入檢查。真正的三種方法重現由 Notebook／`lab.py all` 在每次操作中完成，無需另跑網格或長時間矩陣。
