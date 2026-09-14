# 學生網站來源與建置紀錄

建立日期：2026-09-14。

## 內容依據

- 使用者指定 `26_HydraulicJump_Project/` 為主要 repository，`gc1991-lab/` 為其中一項工作，首頁留在主資料夾。
- 主研究目錄的 `org/student_research_map.org`（2026-09-04 規劃）提供 18 週路線、學生與教師責任、5–9 案例的小型研究方向。
- `org/research_os.org` 與 `org/project.org` 截至 2026-09-14 的狀態提供已備妥教材及尚待準備的工作。後續週次屬規劃；當前固定 GC1991 教材不開放案例參數研究或網格作業。
- `gc1991-lab/README.md`、九份教學文件、既有比較圖及 `CHECKSUMS.json` 提供實驗入口、公式、操作、限制與下載內容。
- 研究幾何圖由網站以 SVG 描繪，明確標示概念示意；不是模擬或量測結果。

原教學發行的 45 個檔案保持原位、內容不變。網站新入口不在舊版校驗表或下載 ZIP 中；原版原始碼、數值設定、資料與參考結果均未修改。

## 網站相依套件

| 元件 | 用途 | 固定版本／來源 |
|---|---|---|
| Python-Markdown | 將既有 Markdown 轉成 HTML | 3.8.2，PyPI；僅建置使用 |
| MathJax | 顯示教材公式 | 3.2.2，npm 官方套件的 `es5/tex-svg.js`，Apache-2.0 聲明見 `assets/vendor/mathjax/LICENSE` |

MathJax 檔案取自 `https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-svg.js`，已保存於 repository。其本地授權檔一併保留。其餘頁面樣式與導覽不依賴外部網頁服務。

## 檢查與範圍

- `scripts/check_site.py` 檢查發布內容的頁面標題、語言、主標題、資源連結、相對路徑、錨點、文件公式與 ZIP 內容及 SHA-256。
- 瀏覽器檢查涵蓋桌面／手機首頁、導覽、GC1991 分頁、中文文件與 MathJax 公式。
- 本次未重新執行水理求解或新的精度矩陣；延用既有教學驗收證據。
- Windows／WSL 和 Intel Mac 尚未實機驗收；HEC-RAS 及坡度轉折教材仍待教師提供。
