# macOS 安裝

需要 Python 3.10 以上與 Apple 命令列開發工具。本版已在 macOS／Apple Silicon 實機驗證，詳細版本見[驗證紀錄](verification.md)。Intel Mac 尚未實機測試。

## 1. 準備工具

開啟「終端機」，檢查：

```bash
python3 --version
xcode-select -p
```

若沒有開發工具，執行下面指令並完成安裝視窗：

```bash
xcode-select --install
```

若沒有 Python，或版本低於 3.10，請安裝 [Python 官方 macOS 套件](https://www.python.org/downloads/macos/)，再重新開啟終端機確認 `python3 --version`。Python 3.12 可作為教學環境選擇；勿只依賴作業系統提供的舊版 Python。

## 2. 放置教材

將 `gc1991-lab-v1.zip` 解壓縮，把其中的 `gc1991-lab` 資料夾移到個人家目錄。完整路徑須為 ASCII 且不含空白，例如 `~/gc1991-lab`。Basilisk 編譯工具會把路徑寫入編譯參數，因此不要放在有空白或中文字的資料夾。

```bash
cd ~/gc1991-lab
bash setup.sh
```

第一次需網路下載 Python 套件。安裝器把 Basilisk 編譯到教材的 `.tools/`，Python 套件放在 `.venv/`，不改動既有 Basilisk 安裝或全域 PATH。等待出現 `Installation checks passed`。

## 3. 開始操作

```bash
bash start_lab.sh
```

把終端機顯示的完整 localhost 網址貼入瀏覽器，依[操作指南](quickstart.md)執行。服務只監聽本機。每次上課重新執行這一指令即可。

若移動或改名教材資料夾，請重新執行 `bash setup.sh`；編譯器及 Python 虛擬環境可能含舊路徑。安裝失敗時查閱[疑難排解](troubleshooting.md)，不要對整個教材使用 `sudo`。
