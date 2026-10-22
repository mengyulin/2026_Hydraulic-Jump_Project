# 網站維護

主 repository：<https://github.com/mengyulin/2026_Hydraulic-Jump_Project>

學生首頁：<https://mengyulin.github.io/2026_Hydraulic-Jump_Project/>

## 檔案配置

```text
index.html                    主專題首頁
README.md                     GitHub repository 首頁說明
assets/                       全站樣式、導覽與本地 MathJax
slope-lab/                    v1.3 封存教學來源與本地 KaTeX
docs/slope-site/              精簡的線上閱讀內容
docs/verification/            GC1991 與坡度 Windows／WSL 驗收紀錄
scripts/integrate_slope.py    坡度教材、導覽與驗收附錄組裝
gc1991-lab/                    原教學工作項目，新增 index.html 入口
guides/gc1991/                 從既有 Markdown 產生的九份網頁
docs/research-plan/            兩組研究規劃與共同比對的可編輯 Markdown
research-plan/                 從上述規劃產生的三份學生網頁
downloads/                    固定教材 ZIP 與 SHA-256
scripts/build_site.py         文件轉換、教材打包與發布內容組裝
scripts/check_site.py         靜態頁面／連結／下載檢查
.github/workflows/pages.yml   GitHub Pages 建置與發布
```

所有站內連結使用相對路徑，支援 GitHub 專案網址的 `/2026_Hydraulic-Jump_Project/` 前綴。首頁不轉址到實驗室。

兩組的目標、工作、成果與比對規則維護在 `docs/research-plan/`，再由原建置指令產生 `research-plan/`；不要只修改產生後的 HTML。首頁包含兩組入口與學期表，週次若變更應同步更新首頁。研究端 `org/student_two_group_plan.org` 和 `org/student_research_map.org` 是規劃依據；網站保留可獨立維護的學生版本，不依賴本機研究資料夾。

目前 2026-10-22 規劃以坡度 P0 為共同基準，兩組各五人。第一組計算標準步法、Saint-Venant 與 Boussinesq 型模型；第二組比對 Python 標準步法與 HEC-RAS 6.6。HEC 實際計算仍待驗收。

組別自 2026-10-14 起為第一組「水躍之深度平均模擬」、第二組「水躍之工程水理分析」。這些頁面、網站導覽與首頁不屬於封存的 45 個教材檔案；更新規劃不需要改動 `CHECKSUMS.json`、核心程式或參考結果。

## 修改內容

- 編輯 `index.html` 更新主題、工作項目、週次與資源。
- 編輯 `gc1991-lab/index.html` 更新實驗入口的網頁導覽。
- 網頁文件由 `gc1991-lab/docs/*.md` 和 `THIRD_PARTY_NOTICES.md` 產生；不要只改 `guides/` 的結果檔。
- GC1991 的 `CHECKSUMS.json` 列出目前接受版本的 45 個教學檔案。改動檔案後，建置會停止；須先審閱差異、記錄修訂範圍與驗證，再更新對應的校驗值。不可只改校驗值來掩蓋改動。
- 單純編輯網站不改動任何求解器、實驗資料或封存參考結果。教材 ZIP 僅包含校驗表所列 45 個檔案與校驗表，不帶入依賴主網站的 HTML 入口。

## 教材修訂紀錄

GC1991 下載仍為 **v1／2026-09-16 Windows 安裝說明修訂版**。依教師要求重寫初學者操作流程，核對官方來源與教材腳本，補上逐步檢查及排錯。與前一版相比，只有 Windows 安裝文件改動，其餘 44 個教材檔案不變。詳見 [本次修訂紀錄](releases/2026-09-16-windows.md)；前次方法章擴充見 [2026-09-15 紀錄](releases/2026-09-15-methods.md)。

- `downloads/gc1991-lab-v1.zip` 是目前接受版本；同目錄的 `zip-sha256.txt` 是其指紋。
- `downloads/archive/` 保留 2026-09-14 與 2026-09-15 的 ZIP 及各版校驗表。
- 若日後變更計算核心、案例輸入或參考結果，須重新執行相應數值驗收；文件修訂不改動或重算原始參考資料；平台安裝檢查只用既有固定案例驗證可重現性。

## 坡度教材 v1.3 與驗收附錄

- `slope-lab/CHECKSUMS.json` 核對 241 個封存來源，`downloads/slope-lab-v1.3.zip` 是實際 Windows／WSL 驗收版本，不在網站建置時重新打包。
- `scripts/integrate_slope.py` 產生網站入口、導覽、去重內容與後續 WSL 狀態；`docs/slope-site/` 維護線上專用段落。封存來源保持原樣。
- `docs/verification/slope-wsl-2026-10-22/` 發布到 `verification/slope-wsl/`。保留原始實算與環境證據，不能將 HEC 檔案往返視為 HEC 求解通過。
- `.github/workflows/check-slope-wsl.yml` 可手動重跑接續安裝驗收；原 GC1991 的 `check-wsl.yml` 保留。兩者都不會部署網站。
- 正式建置不要設定 `SITE_REVIEW=1`；此選項只供本機加上審閱稿橫幅。
- 詳見 [v1.3 正式發布紀錄](releases/2026-10-22-slope-wsl.md)。

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

## Windows／WSL 安裝檢查

`.github/workflows/check-wsl.yml` 是手動執行的檢查，在標準 `windows-2025` runner 安裝 Ubuntu 24.04，以 Linux 家目錄的一般使用者解壓並執行完整教材 ZIP。檢查包括安裝、三種既有方法、Jupyter API、教材核心及 Windows 端 localhost 連線。

執行結果與未通過的步驟應保留，不能把「已建立檢查流程」當成通過。它也不能取代 Windows 11 桌面上的首次帳號設定、重開機、檔案總管與瀏覽器人工操作驗收。此流程僅 `workflow_dispatch` 觸發，不在每次文件編輯時自動重跑。

## 加入下一個工作項目

將新教材放在自己的子資料夾，建立該工作項目的入口；在主首頁工作項目區新增連結與真實的準備狀態，並在 `build_site.py` 的發布範圍明確加入新檔案。完成瀏覽器檢查後再發布，避免將個人環境、完整研究輸出或未準備好的案例一起上傳。

## 2026-10-22 坡度教材整合（待核准）

目前研究與下載入口改以P0坡度渠道為主，GC1991保留為獨立驗證教材。
首頁負責導覽；兩組任務與時程維護在docs/research-plan；詳細方程／參數
由坡度講義提供，P0操作則在兩份完整示範。

slope-lab是v1.3離線包的來源副本，檔案與CHECKSUMS保持一致；已做macOS驗收，Windows／WSL與HEC引擎仍待實機檢查。
downloads/slope-lab-v1.3.zip是本次下載；舊v1.2包另留原位，不覆寫。
scripts/integrate_slope.py在組裝_site時加入全站導覽、精簡網頁重複敘述，
並套用docs/slope-site的網頁內容；不要直接改_site或重寫封存檔案。

一般建置沿用build_site.py與check_site.py。設定環境變數SITE_REVIEW=1
可在本地頁面上顯示「本地審閱稿，尚未發布」；未設定時不插入該提示。
本次沒有推送。核准後才同步本地審閱來源至主repository，檢查差異並發布。


## 2026-10-22：既有Windows／WSL接續安裝（本機審閱）

兩組以GC1991已完成的Ubuntu為主要路線，新增獨立環境、P0啟動與HEC檔案來回複製步驟。
新版v1.3已做macOS全新安裝、兩份P0 Notebook、兩個啟動器及Windows文字格式測試。
Linux／Python3.12僅做目標輪檔解析，不能視為WSL實跑。
待使用者核准後才同步正式repository與發布；沒有執行GitHub workflow。
