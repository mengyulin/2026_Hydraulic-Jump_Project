# Windows 安裝（WSL 2／Ubuntu）

本教材在 Ubuntu 環境編譯 Basilisk。請使用 Windows 11，或支援 WSL 的 Windows 10（版本 2004、組建 19041 以上）。以下流程依 [Microsoft 官方指南](https://learn.microsoft.com/en-us/windows/wsl/install)整理；本版尚未在 Windows 實機跑完，教師宜先用一台學生電腦確認。

## 1. 安裝 Ubuntu

以系統管理員身分開啟 PowerShell，執行：

```powershell
wsl --install -d Ubuntu-24.04
```

依提示重新啟動電腦，開啟 Ubuntu，建立自己的使用者名稱和密碼。輸入 Linux 密碼時畫面不顯示字元是正常現象。若已安裝 Ubuntu，可直接使用；在 PowerShell 用 `wsl --list --verbose` 確认 VERSION 為 2。

此後本頁的指令均在 **Ubuntu 終端機**執行。

## 2. 安裝必要工具

```bash
sudo apt-get update
sudo apt-get install -y build-essential gawk python3 python3-venv unzip
```

`sudo` 會要求剛才設定的 Ubuntu 密碼。這些是系統工具，通常只需安裝一次。

## 3. 放置教材

先在 Ubuntu 執行 `explorer.exe .`，開啟目前 Linux 家目錄的檔案視窗。把教材 ZIP 放入這裡，然後在 Ubuntu 解壓縮：

```bash
unzip gc1991-lab-v1.zip
cd gc1991-lab
```

ZIP 預設包含 `gc1991-lab/` 目錄。路徑請使用英文字母且不含空白，例如 `~/gc1991-lab`。建議放在 Linux 家目錄，避免在 `/mnt/c/`、OneDrive、中文或含空白的路徑編譯。

若日後從 GitHub 下載得到不同名稱的目錄，先將包含 `README.md` 和 `setup.sh` 的那一層改名為 `gc1991-lab`，再使用上面的路徑。

## 4. 安裝教材環境並開啟 Notebook

```bash
bash setup.sh
bash start_lab.sh
```

第一次需要網路下載 Python 套件。Basilisk 原始碼已隨教材附上，安裝器先查核 SHA-256，再在教材的 `.tools/` 內編譯；Python 套件放在 `.venv/`。不必另外安裝全域 Basilisk。

將終端機顯示的 `http://localhost:8888/lab?token=...`（連接埠可能不同）完整貼入 Windows 瀏覽器。保留該終端機，接著依[操作指南](quickstart.md)執行。完成後儲存 Notebook，回到終端機按 Ctrl+C 停止服務。

## 之後每次上課

開啟 Ubuntu，執行：

```bash
cd ~/gc1991-lab
bash start_lab.sh
```

如系統停用虛擬化或 WSL，請按 Microsoft 指引或請系所電腦管理人員協助；Python 套件的安裝不能解決 WSL 系統設定問題。
