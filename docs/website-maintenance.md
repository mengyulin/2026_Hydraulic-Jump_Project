# 網站維護

主 repository：<https://github.com/mengyulin/2026_Hydraulic-Jump_Project>

學生首頁：<https://mengyulin.github.io/2026_Hydraulic-Jump_Project/>

## 檔案配置

```text
index.html                    主專題首頁
README.md                     GitHub repository 首頁說明
assets/                       全站樣式、導覽與本地 MathJax
gc1991-lab/                    原教學工作項目，新增 index.html 入口
guides/gc1991/                 從既有 Markdown 產生的九份網頁
downloads/                    固定教材 ZIP 與 SHA-256
scripts/build_site.py         文件轉換、教材打包與發布內容組裝
scripts/check_site.py         靜態頁面／連結／下載檢查
.github/workflows/pages.yml   GitHub Pages 建置與發布
```

所有站內連結使用相對路徑，支援 GitHub 專案網址的 `/2026_Hydraulic-Jump_Project/` 前綴。首頁不轉址到實驗室。

## 修改內容

- 編輯 `index.html` 更新主題、工作項目、週次與資源。
- 編輯 `gc1991-lab/index.html` 更新實驗入口的網頁導覽。
- 網頁文件由 `gc1991-lab/docs/*.md` 和 `THIRD_PARTY_NOTICES.md` 產生；不要只改 `guides/` 的結果檔。
- GC1991 的 `CHECKSUMS.json` 列出目前接受版本的 45 個教學檔案。改動檔案後，建置會停止；須先審閱差異、記錄修訂範圍與驗證，再更新對應的校驗值。不可只改校驗值來掩蓋改動。
- 單純編輯網站不改動任何求解器、實驗資料或封存參考結果。教材 ZIP 僅包含校驗表所列 45 個檔案與校驗表，不帶入依賴主網站的 HTML 入口。

## 教材修訂紀錄

目前下載為 **v1／2026-09-15 方法文件修訂版**。依教師要求擴寫方法章，逐項核對方程與固定程式、執行文件中的計算例，再更新方法文件的校驗值；其餘 44 個教材檔案不變。詳見 [修訂紀錄](releases/2026-09-15-methods.md)。

- `downloads/gc1991-lab-v1.zip` 是目前接受版本；同目錄的 `zip-sha256.txt` 是其指紋。
- `downloads/archive/` 保留 2026-09-14 的原版 ZIP 與原版校驗表。
- 若日後變更計算核心、案例輸入或參考結果，須重新執行相應數值驗收；本次純方法文件擴充不重跑 CFD／參數矩陣。

## 本機重建與預覽

在主 repository 資料夾執行：

```bash
python3 -m venv .site-venv
.site-venv/bin/pip install -r requirements-site.txt
.site-venv/bin/python scripts/build_site.py
.site-venv/bin/python scripts/check_site.py
python3 -m http.server 8765 --bind 127.0.0.1 --directory _site
```

開啟 `http://127.0.0.1:8765/`。`_site/` 是組裝後的發布內容；它不納入 Git，且每次重建會重建此目錄。請勿在其中保存其他檔案。

Markdown 3.8.2 僅在建置時使用。網站為靜態 HTML，不需要網頁伺服器執行 Python。轉換時保護行內與獨立 TeX 公式，保留程式碼區塊原文。較長公式可水平捲動，方法頁提供章節導覽。MathJax 3.2.2 與 SVG 字形包含於本地資源，公式不依賴外部 CDN；Basilisk／Notebook 仍由學生在自己的電腦執行。

## GitHub Pages

在 repository 的 **Settings → Pages → Build and deployment → Source** 選 **GitHub Actions**。推送 `main` 或在 Actions 手動執行 **Publish student website**，即可建置並發布；pull request 只做檢查。

流程會檢查所有站內文件與錨點、核對目前接受的教材指紋、組裝 `_site/`，最後發布。發布目錄的最上層包含主首頁 `index.html`，因此網站首頁不會落到 `gc1991-lab/`。

設定依據：[GitHub Pages 官方自訂工作流程文件](https://docs.github.com/en/pages/getting-started-with-github-pages/using-custom-workflows-with-github-pages)。

## 加入下一個工作項目

將新教材放在自己的子資料夾，建立該工作項目的入口；在主首頁工作項目區新增連結與真實的準備狀態，並在 `build_site.py` 的發布範圍明確加入新檔案。完成瀏覽器檢查後再發布，避免將個人環境、完整研究輸出或未準備好的案例一起上傳。
