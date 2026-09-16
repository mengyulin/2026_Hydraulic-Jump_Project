# Windows／WSL 安裝：從第一次開啟終端機開始

本頁帶你在 Windows 安裝 Ubuntu，準備水躍教材，並在瀏覽器中開啟 Notebook。**第一次依序完成第 1–8 步；之後上課只需第 9 步。**

**核對日期：2026-09-16。**步驟已對照 Microsoft、Ubuntu 官方文件與教材程式。**Windows／WSL 雲端測試已通過教材安裝、三種計算方法與 Notebook 連線檢查。**學生 Windows 11 電腦上的首次啟用、重開機與桌面操作尚未人工驗收；請依每一步的完成判準檢查，詳細範圍見[本次驗證紀錄](https://github.com/mengyulin/2026_Hydraulic-Jump_Project/blob/main/docs/releases/2026-09-16-windows.md)。

## 本章導覽

- [先認識：我現在在哪個視窗？](#windows-and-ubuntu)
- [1. 準備 Windows 與網路](#prepare)
- [2. 安裝 WSL 2 與 Ubuntu](#install-wsl)
- [3. 重新開機後，開啟 Ubuntu 並建立帳號](#open-ubuntu)
- [4. 確認使用 WSL 2](#check-wsl)
- [5. 安裝 Ubuntu 所需工具](#ubuntu-tools)
- [6. 下載教材，放到 Linux 家目錄並解壓縮](#get-materials)
- [7. 安裝教材環境](#setup-lab)
- [8. 在 Windows 瀏覽器開啟 Notebook](#start-notebook)
- [9. 每次上課如何開始與結束](#next-class)
- [遇到問題：依停住的位置處理](#help)
- [核對來源與驗收範圍](#sources)

<a id="windows-and-ubuntu"></a>

## 先認識：我現在在哪個視窗？

你仍使用原本的 Windows 桌面。**WSL** 是讓 Windows 執行 Linux 環境的功能；**Ubuntu** 是本教材選用的 Linux 發行版。教材的計算程式在 Ubuntu 中執行，Notebook 的操作畫面則由 Windows 的 Edge、Chrome 或其他瀏覽器開啟。

| 名稱 | 本教材用它做什麼？ | 如何辨認？ |
|---|---|---|
| PowerShell | 安裝、啟動及查看 WSL | 提示字串通常以 `PS C:\…>` 開頭 |
| Ubuntu 終端機 | 安裝 Linux 工具、編譯教材、啟動 Notebook | 通常顯示 `使用者@電腦名稱:所在位置$` |
| Windows Terminal（終端機） | 容納上述不同命令列的視窗／分頁 | 視窗名稱本身不能判斷目前是 PowerShell 還是 Ubuntu |
| Windows 瀏覽器 | 操作 Notebook、查看圖表 | 使用 Ubuntu 終端機給你的本機網址 |

**重要：**在 PowerShell 執行啟動 Ubuntu 的指令後，同一個視窗就可能切換成 Ubuntu。請看提示字串及本頁標示的「執行位置」，不要只看視窗顏色。

### 輸入指令的四個習慣

1. **一次輸入一行，按 Enter，等這一步完成再做下一步。**輸出文字還在捲動時通常仍在工作；除啟動 Notebook 服務外，完成後會重新出現可輸入的提示字串。
2. 只複製標為「執行」的指令。範例中的 `PS C:\…>`、`student@…$` 及「示意輸出」都不用輸入。
3. 保留英文半形字元、空格與大小寫。例如 `--install` 是兩個短橫線，`explorer.exe .` 的最後有「空格＋句點」。Linux 檔名區分大小寫。
4. 在 Windows Terminal 可用 **Ctrl+Shift+V** 貼上；若無反應，可試在命令列按滑鼠右鍵。複製終端機文字時先反白，再用 Ctrl+Shift+C。**Ctrl+C 通常是中斷正在執行的程式**。

<a id="prepare"></a>

## 1. 準備 Windows 與網路

本頁以 **Windows 11、Ubuntu 24.04 LTS、WSL 2** 為教學環境。需要可連網、可安裝系統功能的 Windows 帳號，並為 Ubuntu 與教材保留磁碟空間。

若不確定 Windows 版本：按 **Windows 鍵＋R**，在「執行」視窗輸入 `winver` 後按 Enter，即可查看。Microsoft 的簡易 WSL 安裝指令最低支援 Windows 10 2004／組建 19041；Ubuntu 目前的 WSL 指南對 Windows 10 列出至少 21H2。若使用較舊的 Windows，先請教師或電腦管理人員確認環境，再繼續。[Microsoft 安裝要求](https://learn.microsoft.com/en-us/windows/wsl/install)、[Ubuntu 安裝要求](https://ubuntu.com/wsl/docs/latest/howto/install-ubuntu-wsl2/)。

安裝時請使用之後上課會登入的同一個 Windows 帳號。若學校電腦需要另一位管理員的帳號才能安裝，請管理員協助；WSL 的 Linux 安裝與 Windows 使用者有關，不要自行切換帳號反覆安裝。

**本步完成：**確認可用的 Windows 版本、網路及安裝權限，並先儲存手邊工作，準備依提示重新開機。

<a id="install-wsl"></a>

## 2. 安裝 WSL 2 與 Ubuntu

### 2.1 開啟「系統管理員」PowerShell

1. 按 Windows 鍵，搜尋 **PowerShell**。
2. 在「Windows PowerShell」搜尋結果上按滑鼠右鍵，選 **以系統管理員身分執行**。
3. 若跳出使用者帳戶控制視窗，確認是你剛啟動的程式後選「是」。標題通常會包含「系統管理員」或 `Administrator`。

**執行位置：PowerShell（系統管理員）。**

```powershell
wsl --install -d Ubuntu-24.04
```

這行會安裝所需的 WSL 元件，並指定 Ubuntu 24.04。`-d` 表示選擇發行版名稱；單獨使用 `wsl --install` 會選預設發行版，未必與本課程指定版本相同。[Microsoft 安裝指令](https://learn.microsoft.com/en-us/windows/wsl/install)。

### 2.2 等待完成，再依提示重新啟動

安裝過程會下載檔案，時間依網路與電腦而異。若提示需要重新啟動，先儲存工作，再從 **開始 → 電源 → 重新啟動** 重開機；單純關閉 PowerShell 視窗不等於重開機。

有些電腦會在此階段直接開啟 Ubuntu 並詢問使用者名稱、密碼，可先按第 3 步完成設定；有些則只先啟用 WSL 元件，重開機後才繼續安裝 Ubuntu。兩種情況都可能發生。若出現錯誤，先看[問題處理](#help)，不要直接跳到教材安裝。

**已裝過 Ubuntu 的同學：**先在 PowerShell 用 `wsl --list --verbose` 查看名稱。若已有課程指定的 `Ubuntu-24.04`，不用重複安裝；若名稱不同，按第 4 步的說明核對版本，不要刪除原本的 Linux 資料。

**本步完成：**WSL 安裝程序已結束，且已完成它要求的重新啟動。

<a id="open-ubuntu"></a>

## 3. 重新開機後，開啟 Ubuntu 並建立帳號

### 3.1 用指令開啟 Ubuntu

重新登入 Windows 後，按 Windows 鍵搜尋 **PowerShell**，這次直接點選「開啟」，**不必選系統管理員**。

**執行位置：PowerShell（一般使用者）。**

```powershell
wsl -d Ubuntu-24.04
```

這是「開啟已安裝的 Ubuntu」，不是重新安裝。若系統回報找不到此名稱，先看下方的「找不到 Ubuntu」處理方式。

也可在 Windows「開始」搜尋 **Ubuntu**，開啟對應的 **Ubuntu 24.04 LTS**；若沒有找到圖示，仍可使用上面的 PowerShell 指令。以下以從 PowerShell 開啟的流程繼續。[Ubuntu 官方啟動方式](https://ubuntu.com/wsl/docs/latest/howto/install-ubuntu-wsl2/)。

### 3.2 第一次設定 Linux 帳號

第一次啟動可能會先解壓縮或初始化。接著依畫面要求設定：

- **使用者名稱：**例如 `student`。請使用英文小寫字母與數字，以字母開頭，不含中文或空白；這也能讓後續教材路徑符合編譯要求。不必與 Windows 帳號同名。
- **密碼：**輸入自己記得的 Linux 密碼，按 Enter，再輸入一次確認。**畫面不顯示字元、圓點或星號是正常的**。之後執行 `sudo` 時要輸入這個密碼，並非 Windows PIN。

提示文字可能是 `Enter new UNIX username`、`Create a default Unix user account`、`New password` 等，會隨版本不同。若已建立過帳號，之後通常直接進入命令列，不會每次重建。[Microsoft 帳號設定說明](https://learn.microsoft.com/en-us/windows/wsl/setup/environment)。

**示意輸出，不用輸入：**

```text
student@DESKTOP-ABC:~$
```

看到類似的「使用者名稱＠電腦名稱」提示，表示已進入 Ubuntu。這裡使用文字命令列操作；沒有出現另一個 Ubuntu 桌面是正常的。末尾的 `$` 不是要你輸入的指令。從 PowerShell 啟動時，位置也可能顯示 `/mnt/c/Users/…`；第 5 步會明確切回 Linux 家目錄。

**本步完成：**Ubuntu 可開啟，Linux 使用者名稱與密碼已設定，並出現可輸入指令的提示字串。

<a id="check-wsl"></a>

## 4. 確認使用 WSL 2

先離開剛才的 Ubuntu 命令列，回到 PowerShell。

**執行位置：Ubuntu。**

```bash
exit
```

若你是從 PowerShell 開啟 Ubuntu，應會回到 `PS C:\…>`；若從「開始」的 Ubuntu 圖示開啟，視窗可能直接關閉，此時另外開啟一般 PowerShell 即可。

**執行位置：PowerShell。**

```powershell
wsl --list --verbose
```

**示意輸出，不用輸入：**

```text
  NAME             STATE           VERSION
* Ubuntu-24.04     Stopped         2
```

請核對：

- `NAME` 有 `Ubuntu-24.04`。
- `VERSION` 是 **2**，表示使用 WSL 2；它不是 Ubuntu 的版本號。
- `STATE` 顯示 `Running` 或 `Stopped` 都可以。`Stopped` 只是目前未執行，不代表安裝失敗；星號只表示預設發行版。

若 `VERSION` 是 1，或列表沒有 Ubuntu，請先按[問題處理](#help)修正，再往下做。指令定義見 [Microsoft WSL 指令表](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)。

**接著在 PowerShell 再次開啟 Ubuntu：**

```powershell
wsl -d Ubuntu-24.04
```

若先前已安裝的名稱是 `Ubuntu`，而非 `Ubuntu-24.04`，啟動時應使用列表中的實際名稱。進入後可在 **Ubuntu** 執行 `cat /etc/os-release` 查看系統版本；若不是課程指定的 24.04，先與教師確認。下文的 `Ubuntu-24.04` 都是發行版名稱，不能在不核對的情況下套用到另一份安裝。

**本步完成：**列表顯示 WSL 2，並已重新進入 Ubuntu。第 5–7 步的指令全部在 Ubuntu 執行。

<a id="ubuntu-tools"></a>

## 5. 安裝 Ubuntu 所需工具

### 5.1 先回到 Linux 家目錄

「家目錄」是你在 Ubuntu 中的個人資料夾，通常是 `/home/你的Linux使用者名稱`；`~` 是它的簡寫。它與 Windows 的「下載」或「桌面」不同。

**執行位置：Ubuntu。逐行執行。**

```bash
cd ~
pwd
```

`cd` 是切換資料夾，`pwd` 是顯示目前位置。若你的 Linux 使用者叫 `student`，應看到 `/home/student`。若仍在 `/mnt/c/…`，表示還在 Windows 磁碟的路徑，請重新執行 `cd ~`。[Ubuntu 工作目錄說明](https://ubuntu.com/wsl/docs/latest/howto/install-ubuntu-wsl2/)。

### 5.2 安裝編譯工具與 Python

**執行位置：Ubuntu。先完成第一行，再執行第二行。**

```bash
sudo apt-get update
sudo apt-get install -y build-essential gawk python3 python3-venv unzip
```

第一行更新 Ubuntu 的套件清單；第二行安裝教材需要的工具。`sudo` 表示這次以 Linux 管理權限執行，要求密碼時輸入第 3 步設定的 Linux 密碼，畫面依然不顯示字元。`-y` 是自動同意套件安裝的確認詢問。

| 套件 | 用途 |
|---|---|
| `build-essential` | 提供 C 編譯器、make 等建置工具 |
| `gawk` | Basilisk 建置需要的文字處理工具 |
| `python3` | 執行 Python 教材 |
| `python3-venv` | 建立教材專用的 Python 環境 |
| `unzip` | 解壓縮教材 ZIP |

Ubuntu 24.04 的 Python 3.12 系列符合本教材要求的 Python 3.10 以上；`python3-venv` 是另外列出的套件，不能只安裝 `python3`。[Ubuntu 套件資料](https://packages.ubuntu.com/noble/python3-venv)。

### 5.3 確認工具可用

**執行位置：Ubuntu。**

```bash
python3 --version
command -v cc make awk ar unzip
```

第一行應顯示 `Python 3.12.x`（修訂號依更新狀態而異）；第二行應列出五個工具的路徑，例如 `/usr/bin/cc`。若前一步有下載失敗、`Unable to locate package` 或這裡少了工具，不要繼續執行教材安裝；先處理網路／套件問題。

**本步完成：**兩項安裝指令沒有錯誤，Python 版本足夠，且五個工具都找得到。

<a id="get-materials"></a>

## 6. 下載教材，放到 Linux 家目錄並解壓縮

### 6.1 在 Windows 瀏覽器下載完整教材 ZIP

點選 [下載完整 GC1991 教材](https://mengyulin.github.io/2026_Hydraulic-Jump_Project/downloads/gc1991-lab-v1.zip)，保存為 **`gc1991-lab-v1.zip`**。通常會存進 Windows「下載」資料夾。這是已整理好的教學包，不需要使用 GitHub 的綠色 Code → Download ZIP。

先保留 ZIP，不在 Windows「下載」資料夾直接解壓。若重複下載造成檔名變成 `gc1991-lab-v1 (1).zip`，請在檔案總管確認完整檔名後改回 `gc1991-lab-v1.zip`。Windows 11 可在 **檢視 → 顯示 → 副檔名** 顯示 `.zip`，避免誤改成 `.zip.zip`。

### 6.2 用檔案總管打開 Ubuntu 家目錄

**執行位置：Ubuntu。逐行執行。**

```bash
cd ~
pwd
explorer.exe .
```

確認 `pwd` 顯示 `/home/你的Linux使用者名稱`，最後一行會以 Windows 檔案總管打開**同一個 Linux 資料夾**。`explorer.exe` 是開啟檔案總管，最後的 `.` 表示「目前資料夾」。網址列通常類似 `\\wsl.localhost\Ubuntu-24.04\home\student`，也可能使用 `\\wsl$\…`。[Microsoft 檔案操作說明](https://learn.microsoft.com/en-us/windows/wsl/filesystems)。

另開一個檔案總管到 Windows「下載」，把剛下載的 ZIP **複製**到這個 Linux 家目錄視窗。複製完成後，回到 Ubuntu 終端機。

### 6.3 確認 ZIP，解壓後進入教材資料夾

**執行位置：Ubuntu。先執行這兩行確認檔案。**

```bash
cd ~
ls -l gc1991-lab-v1.zip
```

`ls` 用來列出檔案。若看到 ZIP 的檔名與大小，才繼續；若顯示 `No such file or directory`，代表檔名或位置不對，回到第 6.2 步確認。

以下適用於**第一次安裝、家目錄尚無 `gc1991-lab` 資料夾**的情況。若已經有舊教材或作業，先保留原資料夾，請教師協助安排新版位置；不要把新 ZIP 直接覆蓋到做過作業的資料夾。

**執行位置：Ubuntu。逐行執行。**

```bash
unzip gc1991-lab-v1.zip
cd ~/gc1991-lab
pwd
ls
```

ZIP 內已包含 `gc1991-lab/` 這一層，不必再多建同名資料夾。`pwd` 應顯示 `/home/你的Linux使用者名稱/gc1991-lab`；`ls` 應看得到 `setup.sh`、`start_lab.sh`、`student_lab.ipynb`、`README.md` 等檔案。

教材會從原始碼編譯工具，因此**完整路徑須使用 ASCII 字元，且沒有空白**。本頁的英文 Linux 帳號與 `~/gc1991-lab` 可符合這項要求。即使 Windows 使用者名稱是中文，也不影響另行建立的英文 Linux 家目錄。請在 Linux 家目錄操作，不在 `/mnt/c/`、OneDrive 或 Windows 桌面編譯教材。

**本步完成：**你在 Linux 的 `gc1991-lab` 資料夾中，並能看到兩個 `.sh` 檔與 Notebook。

<a id="setup-lab"></a>

## 7. 安裝教材環境

**執行位置：Ubuntu。**

```bash
cd ~/gc1991-lab
bash setup.sh
```

`bash setup.sh` 的意思是請 Ubuntu 執行教材的安裝腳本。它會依序：

1. 檢查 Python、工具及資料夾路徑。
2. 查核隨附 Basilisk 原始碼的指紋，編譯到教材內的 `.tools/`。
3. 建立教材專用的 `.venv/`，從網路下載 Python 套件。
4. 註冊 **GC1991 Lab** Notebook 核心，執行安裝檢查。

這一步可能一段時間只顯示 `Building Basilisk…`，因為詳細編譯訊息寫在 `.tools/build.log`；稍後才會顯示套件下載或測試結果。第一次需要網路。**不要在 `bash setup.sh` 前面加 `sudo`**，也不必先在 Windows 安裝 Python、手動安裝全域 Basilisk 或執行 `pip install`。

**安裝成功時的結尾訊息，不用輸入：**

```text
Installation checks passed. Next: bash start_lab.sh
```

只有看到這行、且沒有安裝失敗，才繼續下一步。若提早出現 `Setup failed`、`Error` 或 `Traceback`，先保留錯誤文字，按[問題處理](#help)檢查。修正原因後，在同一個教材資料夾重新執行 `bash setup.sh` 即可，不必重新安裝整個 Ubuntu。

**本步完成：**看到 `Installation checks passed`。這表示環境與快速檢查通過；三種水理方法的完整計算會在 Notebook 中進行。

<a id="start-notebook"></a>

## 8. 在 Windows 瀏覽器開啟 Notebook

### 8.1 啟動 Notebook 服務

**執行位置：Ubuntu。**

```bash
cd ~/gc1991-lab
bash start_lab.sh
```

這次程式會持續執行，**沒有立刻回到 `$` 提示字串是正常的**；這個視窗正在提供 Notebook 服務。教材刻意不自動開啟 Linux 瀏覽器。

### 8.2 複製這次產生的網址

在輸出中找以 `http://localhost:` 或 `http://127.0.0.1:` 開頭、包含 `token=` 的完整網址。

**網址外觀示意，不是可直接使用的網址：**

```text
http://localhost:8888/lab?token=這裡會是一長串字元
```

用滑鼠反白完整網址，再複製到 **Windows 的 Edge／Chrome 網址列**並按 Enter。請使用終端機這次實際給出的網址：連接埠可能是 8889 等其他數字，路徑也可能包含 Notebook 檔名。**不要只複製 `localhost:8888`，也不要使用上面的示意字串或 `file:///…` 連結。**Token 是這次連線的通行碼，求助時不必提供給他人。[Jupyter 的網址與 token 說明](https://jupyter-server.readthedocs.io/en/latest/operators/security.html)。

Windows 通常可以透過 `localhost` 存取 WSL 裡啟動的服務。本教材僅監聽本機 `127.0.0.1`，不需要公開連接埠；若無法連線，先按問題處理逐項確認。[Microsoft WSL 網路說明](https://learn.microsoft.com/en-us/windows/wsl/networking)。

### 8.3 確認 Notebook 和核心

1. 頁面應出現 JupyterLab。若尚未自動打開教材，在左側檔案列表雙擊 **`student_lab.ipynb`**。
2. 若出現核心選擇視窗，選 **GC1991 Lab**。也可在 **Kernel → Change Kernel…** 選擇它。
3. 依[操作指南](quickstart.md)操作；點選第一個程式儲存格，按 **Shift+Enter** 執行。後續計算格會真正執行求解器，請等目前格子完成再繼續。

**保留啟動服務的 Ubuntu 視窗。**只關閉瀏覽器分頁不會停止服務；直接關掉 Ubuntu 視窗則可能讓 Notebook 斷線。

**本步完成：**瀏覽器能開啟 `student_lab.ipynb`，並能選用 GC1991 Lab 核心。

<a id="next-class"></a>

## 9. 每次上課如何開始與結束

### 開始上課：不用重新安裝

先開啟一般 PowerShell。

**執行位置：PowerShell。**

```powershell
wsl -d Ubuntu-24.04
```

提示字串切成 Ubuntu 後，再執行下列兩行。

**執行位置：Ubuntu。**

```bash
cd ~/gc1991-lab
bash start_lab.sh
```

把這次出現的完整 token 網址貼到 Windows 瀏覽器。正常情況下不需重跑 `wsl --install`、套件安裝或 `bash setup.sh`。

### 結束上課：先儲存，再停止服務

1. 在 Notebook 按 **Ctrl+S**，或選 **File → Save Notebook**，確認已儲存。
2. 回到正在執行 `start_lab.sh` 的 Ubuntu 視窗，按 **Ctrl+C**。
3. 若詢問 `Shut down this Jupyter server (y/[n])?`，輸入 **y** 並按 Enter。若已直接回到命令提示字串，就不必再輸入 y。
4. 回到可輸入的 Ubuntu 提示字串後，可輸入 `exit` 離開；之後再關閉瀏覽器與 PowerShell。

作業保存在 Ubuntu 的 `~/gc1991-lab`，計算結果在其中的 `runs/`。要用 Windows 檔案總管查看或備份，可在服務停止後的 **Ubuntu** 執行：

```bash
cd ~/gc1991-lab
explorer.exe .
```

**完成安裝後，你應能做到：**重新開啟 Ubuntu、進入教材資料夾、啟動 Notebook、儲存作業並正常停止服務。

<a id="help"></a>

## 遇到問題：依停住的位置處理

### A. 找不到 Ubuntu，或安裝尚未完成

**執行位置：PowerShell。先查已安裝的名稱。**

```powershell
wsl --list --verbose
```

若列表已出現 Ubuntu，使用該列實際名稱搭配 `wsl -d` 開啟。若明確顯示「沒有已安裝的發行版」，可能只完成了 WSL 元件安裝；請先完成重新開機，再以**系統管理員 PowerShell**執行：

```powershell
wsl --install -d Ubuntu-24.04
```

若已安裝舊版 WSL，卻無法辨認 Ubuntu 24.04 的新版映像，先在**系統管理員 PowerShell**更新：

```powershell
wsl --update
```

依提示完成更新／重開機後重試。若只顯示指令用法，或指定名稱不在列表中，可在 **PowerShell** 用 `wsl --list --online` 核對可安裝名稱。[Ubuntu 安裝格式說明](https://ubuntu.com/wsl/docs/latest/howto/install-ubuntu-wsl2/)。

若下載長時間停在 `0.0%`，先以 Ctrl+C 結束該次安裝，再在**系統管理員 PowerShell**試官方提供的下載途徑：

```powershell
wsl --install --web-download -d Ubuntu-24.04
```

此選項仍需要可用的網路。[Microsoft 安裝問題說明](https://learn.microsoft.com/en-us/windows/wsl/install)。

### B. VERSION 是 1，或顯示虛擬化錯誤

若是已有資料的舊 Ubuntu，先備份重要檔案，再進行 WSL 版本轉換。關閉該 Ubuntu 中正在進行的工作後，在 **PowerShell** 執行（名稱須與列表一致）：

```powershell
wsl --set-version Ubuntu-24.04 2
```

完成後用 `wsl --list --verbose` 再確認。若出現 `0x80370102`、`HCS_E_HYPERV_NOT_INSTALLED` 或要求啟用虛擬化，先確認已依安裝提示重新開機；若仍失敗，請教師／管理人員按 [Microsoft 疑難排解](https://learn.microsoft.com/en-us/windows/wsl/troubleshooting)確認「虛擬機器平台」與 BIOS／UEFI 的硬體虛擬化設定。這是 WSL 層級的問題，重跑教材 `setup.sh` 無法處理。

### C. 已進入 Ubuntu，但某一步失敗

| 看到的情況 | 先做什麼？ |
|---|---|
| PowerShell 說找不到 `sudo`、`apt-get`，或 `bash` 不能正確執行 | 確認不是停在 `PS C:\…>`；先用 `wsl -d Ubuntu-24.04` 進入 Ubuntu。 |
| 密碼輸入後畫面沒有反應 | 密碼本來就不顯示字元；輸入完整後按 Enter。`sudo` 要的是 Linux 密碼，不是 Windows PIN。 |
| `Temporary failure resolving…`、`Failed to fetch…` | Ubuntu 的下載／名稱解析失敗；確認網路及學校代理設定，恢復後先重跑 `sudo apt-get update`，再安裝套件。 |
| `Unable to locate package`、`venv`／`ensurepip` 不存在 | 確認第 5 步的更新成功，並安裝了 `python3-venv`；仍失敗時提供完整錯誤與 Ubuntu 版本。 |
| `explorer.exe` 找不到或未開啟 Linux 資料夾 | 保持 Ubuntu 開啟，在 Windows 檔案總管網址列輸入 `\\wsl$`，選擇發行版 → `home` → 自己的 Linux 使用者資料夾；不要到 Windows 的 AppData 中找檔案。 |
| 找不到 ZIP 或 `setup.sh` | 先用 `pwd`、`ls` 核對位置、完整檔名與解壓層級；`setup.sh` 應在 `~/gc1991-lab`。 |
| 路徑含空白／非 ASCII、找不到 `cc` 或 `make` | 回到第 5–6 步確認英文 Linux 家目錄及工具；不要只換一個 Windows 資料夾繼續試。 |
| `Setup failed`、Basilisk 編譯失敗 | 保留錯誤與教材內 `.tools/build.log`，交給教師查看。不要自行換掉隨附原始碼。 |
| `start_lab.sh` 顯示 `First run: bash setup.sh` | 尚未建立可用的教材環境；先完成第 7 步。 |
| 找不到 GC1991 Lab 核心 | 正常停止舊 Jupyter 服務，確認第 7 步成功後，再從教材內用 `bash start_lab.sh` 啟動。 |

### D. Notebook 網址無法開啟

依序確認：

1. Ubuntu 的服務視窗仍開著，且沒有錯誤或已停止的訊息。
2. 複製的是**本次啟動顯示的完整網址**，包括實際連接埠、路徑及 token；輸入在瀏覽器網址列，不是搜尋框。
3. 若 `localhost` 無法連線，將網址中的 `localhost` 換成 `127.0.0.1` 再試，其他部分保留。
4. 若頁面要求 token，重新複製本次的完整 token 網址。若連線仍被擋住，請教師／管理員檢查 VPN、代理、防火牆或學校政策；不需要把服務改成對外公開。

一般程式錯誤另見[疑難排解](troubleshooting.md)。求助時請提供：**卡在第幾步、執行的指令、完整錯誤文字、Windows 版本**，以及下列資料。

**執行位置：PowerShell。**

```powershell
wsl --list --verbose
```

**若 Ubuntu 還能開啟，執行位置：Ubuntu。**

```bash
cat /etc/os-release
python3 --version
pwd
```

請保留作業與失敗紀錄；不用提供密碼或完整 token 網址，也不要為了排錯解除註冊／刪除 Ubuntu。

<a id="sources"></a>

## 核對來源與驗收範圍

以下為本頁核對時使用的官方來源：

- [Microsoft：安裝 WSL](https://learn.microsoft.com/en-us/windows/wsl/install)及 [WSL 基本指令](https://learn.microsoft.com/en-us/windows/wsl/basic-commands)：安裝、啟動、列出發行版與 WSL 版本。
- [Microsoft：設定 WSL 環境](https://learn.microsoft.com/en-us/windows/wsl/setup/environment)：Linux 帳號、密碼與日常操作。
- [Ubuntu：安裝 Ubuntu on WSL 2](https://ubuntu.com/wsl/docs/latest/howto/install-ubuntu-wsl2/)：Ubuntu 24.04 的安裝名稱、映像格式及啟動目錄。
- [Microsoft：跨檔案系統操作](https://learn.microsoft.com/en-us/windows/wsl/filesystems)與 [WSL 網路](https://learn.microsoft.com/en-us/windows/wsl/networking)：`explorer.exe .`、Linux 家目錄與 Windows 瀏覽器連線。
- [Ubuntu：build-essential](https://packages.ubuntu.com/noble/build-essential)、[python3-venv](https://packages.ubuntu.com/noble/python3-venv)：系統工具與 Python 環境套件。
- [Jupyter Server：token 與連線](https://jupyter-server.readthedocs.io/en/latest/operators/security.html)：使用實際產生的本機網址。
- [Microsoft：WSL 疑難排解](https://learn.microsoft.com/en-us/windows/wsl/troubleshooting)：虛擬化與安裝錯誤。

教材特有的成功訊息、檔名、核心名稱及啟動行為，則對照隨附的 `setup.sh`、`start_lab.sh`、`scripts/setup_basilisk.py` 與 `student_lab.ipynb`。

2026-09-16 已在 **Windows Server 2025／WSL 2／Ubuntu 24.04** 的雲端環境，以一般 Linux 使用者實際完成教材安裝、三種既有方法的計算與參考結果比對、Jupyter 啟動、GC1991 Lab 核心與 Notebook 讀取，以及 Windows 端的本機網址連線。[自動測試結果](https://github.com/mengyulin/2026_Hydraulic-Jump_Project/actions/runs/35079687917)與[完整驗證紀錄](https://github.com/mengyulin/2026_Hydraulic-Jump_Project/blob/main/docs/releases/2026-09-16-windows.md)保留了環境及檢查範圍。

**尚未人工驗收：**學生 Windows 11 電腦上的首次啟用 WSL、重新開機、互動帳號／密碼設定、檔案總管搬移 ZIP，以及瀏覽器內的滑鼠與鍵盤操作。這些步驟已核對官方文件，但雲端測試不能涵蓋每台電腦的畫面或學校設定。網站連結、指令區塊、桌面／手機版面與下載 ZIP 另已檢查。較早的 macOS 測試見 [2026-09-14 本機驗證紀錄](verification.md)。
