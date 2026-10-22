# 水躍學生專題

目前主題是**坡度變化矩形渠道的水躍**。兩組各五人，以P0為共同基準，再各自研究上游坡度、尾水、轉換長度、下游坡度或Manning粗糙度。

- **第一組：** Python標準步法、聖維南淺水方程與定常壓力近似Boussinesq型模型。
- **第二組：** Python標準步法與HEC-RAS 6.6一維定常混合流。

[學生網站](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/)提供線上講義、P0逐步示範、個人操作單及成果繳交格式。程式在學生電腦執行，網站提供閱讀與下載。

## 從這裡開始

1. [問題設定](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/slope-lab/docs/problem.html)與[三種方法](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/slope-lab/docs/methods.html)。
2. [下載教學包v1.3](downloads/slope-lab-v1.3.zip)，沿用已完成GC1991的WSL／Ubuntu，依包內安裝頁加裝坡度套件。兩組皆在Ubuntu執行Python，HEC在Windows計算。
3. [第一組P0示範](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/slope-lab/docs/p0_group_a.html)或[第二組P0示範](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/slope-lab/docs/p0_group_b.html)。
4. 依組別頁與個人操作單進行低、高水準，再整理成果。

## 檢查範圍

Windows Server 2025／WSL 2／Ubuntu 24.04 已通過同一帳號的 GC1991 接續安裝、兩組 P0 Python、Windows 連線與檔案往返。見[實際驗收紀錄](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/verification/slope-wsl/)。

Python三模式已通過P0既有結果重現；重現不等於物理驗證或波形收斂。B波動仍是學生研究內容。HEC-RAS 6.6輸入已準備，但 **HEC-RAS 6.6 實際開檔／計算仍待驗收**，未提供代填的HEC結果。

[GC1991](gc1991-lab/README.md)及原下載ZIP保留作水平渠道驗證教材。原程式、實驗資料與參考結果不因網站整合而變更。

## 維護

詳見[網站維護說明](docs/website-maintenance.md)。坡度教材的封存v1.3來源位於 <code>slope-lab/</code>；網站導覽與去重版本由 <code>scripts/integrate_slope.py</code> 和 <code>docs/slope-site/</code> 在建置時產生，下載ZIP保持原版。

本次經教師核准正式發布，內容與驗收範圍見[2026-10-22 發布紀錄](docs/releases/2026-10-22-slope-wsl.md)。先前[審閱稿紀錄](docs/releases/2026-10-22-slope-integration.md)保留供追溯。
