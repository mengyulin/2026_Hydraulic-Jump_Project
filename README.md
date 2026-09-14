# 水躍學生專題 · Hydraulic Jump Project

從古典水理、共同案例與可重現計算出發，研究渠道由陡坡轉為緩坡時的水躍，並比較 Python、HEC-RAS 與 Basilisk 的工程計算。

**[學生專題網站](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/)** · **[GC1991 實驗室](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/gc1991-lab/)**

網站首頁為主資料夾的 `index.html`。`gc1991-lab/` 是整個學生專題的第一項工作；其中保留原本的 Notebook、程式、資料與教材。

## 現階段工作

| 工作項目 | 狀態 | 內容 |
|---|---|---|
| GC1991 水平渠道實驗 | 教材已備妥；macOS 已測，Windows／WSL 待驗收 | 一本 Notebook 比較 standard-step、Saint-Venant、自訂 M92 |
| 古典水理與坡度轉折 | 待教師提供案例 | 水理公式、急／緩流分支與共同幾何 |
| HEC-RAS 工程比較 | 待教師提供案例 | 匹配輸入、mixed-flow 與斷面間距 |
| 坡度／尾水小型研究 | 完成共同基準後 | 5–9 組受控案例及可重現報告 |

完整 18 週路線、學習資源與交付要求見[主首頁](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/)。

## 學生第一次使用

1. [下載 GC1991 教材 ZIP](downloads/gc1991-lab-v1.zip)，解壓縮至英文且不含空白的路徑。
2. 閱讀 [Windows／WSL](gc1991-lab/docs/install-windows.md) 或 [macOS](gc1991-lab/docs/install-macos.md) 安裝指南。
3. 在 `gc1991-lab/` 執行 `bash setup.sh`，再執行 `bash start_lab.sh`。
4. 開啟 `student_lab.ipynb`，選擇 **GC1991 Lab** 核心並依序執行。

若從 GitHub **Code → Download ZIP** 下載整個 repository，請進入其中的 `gc1991-lab/` 才執行安裝；主資料夾是網站與專題入口。

GC1991 固定教材使用水平底床，尚未涵蓋坡度轉折。程式重現成功不等同實驗驗證；詳見[方法與限制](gc1991-lab/docs/methods.md)。

## 網站維護

- [網站編輯、重建與發布](docs/website-maintenance.md)
- [來源與建置紀錄](docs/site-record.md)
- [GC1991 原始材料與第三方授權](gc1991-lab/THIRD_PARTY_NOTICES.md)

本 repository 未替教師原創程式或文件指定新的概括授權。Basilisk 與網站公式元件各保留隨附聲明。
