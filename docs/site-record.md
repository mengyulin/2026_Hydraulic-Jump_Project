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

## 首次發布

GitHub Pages 已啟用為 GitHub Actions，首次成功發布見 [workflow 34841848744](https://github.com/mengyulin/2026_Hydraulic-Jump_Project/actions/runs/34841848744)。首頁位於主專題網址，GC1991 入口為其中的 `gc1991-lab/`。

線上首頁、實驗入口、方法頁、樣式與完整教材 ZIP 均回傳 HTTP 200，並與本地發布版本逐位元組一致。初次推送的建置檢查已通過，但部署先於 Pages 啟用而停止；啟用後同一版本重發成功。

## 2026-09-15 方法文件擴充

依教師要求，將方法章擴展成 11 節的獨立教材，涵蓋 standard-step、Saint-Venant 與 Boussinesq 的基本方程、推導、實際算法與結果解讀。具體改動、文獻核對、計算例及版本指紋見 [方法文件修訂紀錄](releases/2026-09-15-methods.md)。

本次僅變更原始 45 個教材檔案中的 `docs/methods.md`；其餘 44 檔與首次發行一致。原始 ZIP 與校驗表已另行保存，新 ZIP 同步供學生下載。新增行內 TeX 保護、章節導覽及長公式捲動，54 組獨立公式與 229 處行內公式在桌面及手機上均成功顯示。

## 2026-09-16 初學者 Windows 安裝說明

將 Windows／WSL 安裝重寫為從辨識視窗到開始、結束每次上課的逐步教材。新增 Ubuntu 啟動與帳號設定、WSL 2 檢查、Linux 家目錄、ZIP 搬移、成功訊息及分階段排錯；未加入 Mac 虛擬機議題。

指令與示意輸出明確分開，示意輸出不提供複製按鈕；長篇指南的章節連結使用立即跳轉。完整修訂與驗證範圍見 [2026-09-16 修訂紀錄](releases/2026-09-16-windows.md)。

Windows／WSL 雲端驗證 [35079687917](https://github.com/mengyulin/2026_Hydraulic-Jump_Project/actions/runs/35079687917) 通過安裝、三種既有方法的結果重現、Jupyter 啟動及 Windows localhost 連線；首頁與安裝頁已更新目前狀態。Windows 11 首次啟用及桌面操作仍待人工驗收，較早的 2026-09-14 驗證文件保留為當時紀錄。
