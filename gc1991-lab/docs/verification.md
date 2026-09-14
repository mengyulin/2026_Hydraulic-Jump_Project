# 本機驗證紀錄

日期：2026-09-14。狀態：**macOS 本機發行候選版通過**；Windows／WSL 與 Intel Mac 尚未實機驗證。

## 已測試環境

macOS 26.6.2、Apple Silicon arm64；Apple clang 21.0.0；全新 Python 3.14.5 虛擬環境。完整環境版本表在 [`python-packages-tested.txt`](python-packages-tested.txt)。主要套件為 NumPy 2.5.3、Matplotlib 3.11.2、JupyterLab 4.6.3、nbclient 0.11.0、ipykernel 7.3.0。

從獨立匯出目錄開始，使用隨附原始碼建置 Basilisk，從 PyPI 安裝 Python 依賴，註冊本套件的 Jupyter 核心。第一次下載受測試執行環境的網路限制阻擋；取得網路存取後，同一安裝程序完整通過，沒有放寬依賴條件或改用教師既有虛擬環境。

## 完成項目

- 五項快速檢查通過：共軛水深的動量／能量、standard-step 分支、兩種初始資料的座標與單位、錯誤輸入攔截、實驗比較範圍。
- 六個 Notebook 程式儲存格全部執行成功，輸出兩張內嵌 PNG 圖；Notebook 真的重新執行三種計算。
- `start_lab.sh` 可啟動 JupyterLab，僅監聽 127.0.0.1；本機服務回傳教材 Notebook 與 GC1991 Lab 核心，測試結束後已停止。
- 兩個 C 模式完成指定時間與平均視窗，正水深及原有收支檢查通過。
- 核心與 Notebook 通過 Python 3.10 語法檢查；這項靜態檢查不等於所有舊版 Python／套件組合均已實機測試。
- README 比較圖已檢視，標題、單位、圖例與圖註完整；配送檔案沒有教師私人絕對路徑。相對文件連結與 ZIP 指紋另於發行時核對。

## 獨立目錄的實際結果

| 方法 | 流場／水理計算耗時 | 實驗 RMSE | 對封存基準的差異 |
|---|---:|---:|---|
| Standard-step | 約 0.11 s | 52.216 mm | 跳躍位置差 0 m |
| Explicit SV | 約 12.93 s | 52.196 mm | 最大平均水深差 0 m |
| Custom M92 B on | 約 0.78 s | 14.142 mm | 最大平均水深差 0 m |

耗時不含首次 Basilisk／Python 安裝、C 編譯與繪圖，也不是其他電腦的保證。C 程式首次編譯通常另需約 0.5–1 s。本次預先設定的重現公差未調整：C 水深差 0.2 mm、standard-step 位置差 2 mm；實際結果與基準一致。

完整可讀數值摘要與來源指紋見 [`verification.json`](verification.json)。這些檢查確認教材能運作並重現既有結果，不增加水躍內部流速、滾流或網格收斂的物理宣稱。

原 M92 教學套件、研究驗收結果與失敗紀錄均未改動；舊套件及相關封存資料另以既有檢查工具確認完整。新的三模式教學發行不覆蓋舊套件。
