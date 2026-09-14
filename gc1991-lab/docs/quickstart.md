# 操作指南

完成安裝後，執行 `bash start_lab.sh`，開啟終端機提供的 localhost 網址。雙擊 `student_lab.ipynb`，右上方核心應為 **GC1991 Lab**。用 Shift+Enter 逐格執行，或選 Run → Run All Cells。

## 依序執行的五件事

1. 載入 Test 4，閱讀流量、水深、渠道寬度與計算區域。
2. 執行 standard-step，觀察急流和緩流分支以比力匹配得到的零長度水躍。
3. 執行 Saint-Venant，觀察時間演進後的平均水面。
4. 執行自訂模式，觀察有限寬度的水面上升。
5. 疊合三種結果與實驗，查看各方法的 RMSE。

每個計算格都會顯示 `reproduction passed`。這表示程式重現教材的既有數值結果；它不代表所有方法都與實驗吻合。standard-step 和 SV 的較大誤差正是此比較的學習重點。

Notebook 的三次計算都是重新執行求解器；`reference/` 中的水面僅供核對。最後一格可把圖的 x 範圍改為 `(0, 14)`，查看整段渠道。圖中水深即水面高程，因為此例渠道底床設為 z=0。

## 結果在哪裡

每次計算在 `runs/日期時間_方法_識別碼/` 建立新目錄，包含：

| 檔案 | 用途 |
|---|---|
| `case.json` | 此次實際採用的完整設定 |
| `profile.dat` | 原始數值水面，各模式欄位見檔案第一行 |
| `metadata.json` | 計算耗時、來源指紋、RMSE、重現與完成狀態 |
| `initial.dat`、C 原始碼 | Basilisk 案例的實際初始資料及核心程式副本 |
| `build.log`、`stderr.log` | Basilisk 編譯與執行訊息 |
| `solution.json` | standard-step 的兩條分支、跳躍位置與水深 |

比較圖在另一個 `runs/日期時間_comparison_識別碼/`，含 `comparison.png`、`comparison.pdf` 與記錄來源計算的 `comparison.json`。可直接把圖放進專題報告。重跑不覆蓋先前結果；若曾失敗，也保留該次紀錄。

## 不使用 Notebook

在教材根目錄執行：

```bash
.venv/bin/python lab.py all
```

只跑一個方法：

```bash
.venv/bin/python lab.py standard_step
.venv/bin/python lab.py sv
.venv/bin/python lab.py custom
```

命令列產生相同資料；`all` 會自動保存比較圖。

## 一次課堂即可完成的作業

- 繳交三種方法的比較圖與 RMSE 表，附上各方法的計算設定。
- 用共軛水深與比力說明 standard-step 為何產生突跳。
- 解釋自訂模式水面較接近實驗，為何仍不能宣稱水躍內部流速正確。
- 在 Python 中調整圖的顯示範圍，說明水躍區與下游緩流段的差別。

第一版不要求學生修改 C 核心、加密網格、調整 Manning n 來擬合，或重新跑教師的驗收矩陣。先理解[方法與限制](methods.md)即可。
