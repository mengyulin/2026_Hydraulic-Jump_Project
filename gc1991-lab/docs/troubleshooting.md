# 疑難排解

| 現象 | 處理方式 |
|---|---|
| Windows 找不到 bash 或 make | 使用 Ubuntu／WSL 終端機，依 Windows 安裝頁完成系統工具安裝。 |
| Python 版本低於 3.10 | 安裝較新的 Python，重新開啟終端機；Ubuntu 可使用 24.04 提供的 Python。 |
| 提示路徑含空白／非 ASCII | 將教材放到 `~/gc1991-lab`，重新執行 `bash setup.sh`。 |
| 找不到 cc、make、awk、ar | Mac 完成 Xcode Command Line Tools；Ubuntu 安裝 build-essential 與 gawk。 |
| `venv`／`ensurepip` 不存在 | Ubuntu 安裝 `python3-venv` 後重試。 |
| 套件下載／憑證或網路失敗 | 確認可連網，按 Python 官方安裝程序處理憑證，重新執行 setup；不要關閉 HTTPS 憑證驗證。 |
| Basilisk 編譯失敗 | 閱讀 `.tools/build.log`；教材內的原始碼快照有校驗，不應自行換成網站最新版本。 |
| Notebook 找不到 numpy 或 lab | 確認工作目錄是教材根目錄、核心選 GC1991 Lab，並用 `bash start_lab.sh` 啟動。 |
| 找不到 GC1991 Lab 核心 | 重新執行 setup，關閉舊 Jupyter 服務後再啟動。 |
| 移動教材後不能執行 | 重新執行 setup 讓編譯路徑更新。如仍使用舊 Python 路徑，先把 `.venv` 改名備份，再執行 setup。 |
| 瀏覽器要求 token | 使用終端機顯示的完整 localhost 網址；不要只複製連接埠。 |
| 顯示 fixed Test 4／參數檢查失敗 | 還原 `cases/test4.json`；本版只驗收固定案例，不能把改參數後的結果當成同一基準。 |
| 顯示 reference depth error 或 solver failed | 保留此次 runs 目錄，交給教師查看 metadata、build.log、stderr.log；不要改容許值來消除訊息。 |

學生應提供錯誤文字、作業系統、Python 版本與該次 `metadata.json`。無需交出整個 `.tools/` 或 `.venv/`。SV 通常比另兩種方法久；程式逾時保護為單次流場 300 秒，避免失敗後無限等待。

若只想閱讀結果，README 已有預期圖；這張圖不會取代 Notebook 的重新計算。原始失敗結果保留在本機 `runs/`，不會被下一次重跑覆蓋。
