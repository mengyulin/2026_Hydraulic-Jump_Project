# 教師維護與發行

## 本版範圍

v1 是固定 Test 4 教學案例：先比較 classical standard-step、顯式 SV 與自訂 M92。採用既有水理、時間步、平均及初始條件驗收證據，不重新開啟 GN，也不增加學生的網格精度任務。

`cases/test4.json` 是實際運算輸入；`reference/expected.json` 保存獨立的接受設定。程式檢查兩者一致，避免改錯參數後仍顯示通過。學生可修改 Notebook 的繪圖、單位換算與數據分析。若日後要做參數研究，教師應新增明確案例與適用範圍，再另行開放輸入，不能直接更新參考值把未驗證結果變成「通過」。

## 必要且有限的驗收

- `python -m unittest discover -s tests -v`：快速公式、分支、初始資料與輸入檢查。
- `python lab.py all`：實際編譯並完成三種計算，檢查正水深、預定平均時段及原有全域收支。
- 與封存水面比較：C 模式最大水深差容許 0.2 mm；standard-step 跳躍位置差容許 2 mm。這是安裝重現公差，不是實驗誤差要求，也不改寫先前研究的網格門檻。
- 從全新匯出資料夾執行 Notebook（`python scripts/check_notebook.py`），確認不依賴研究專案、教師絕對路徑或全域 qcc。

三種方法通過後即結束本版驗收，不自動展開更細網格。以前的 M184 形狀變化、M368 拒絕及強稀疏波失敗仍保留為限制，不能因教學用途宣稱一般求解器已通過物理驗證。

## 原始碼與套件

- `core/`：核心水理程式；除了移除未啟用的 GN 區塊，保留研究來源的數值程式。
- `vendor/`：約 9 MB 的完整 Basilisk 官方原始碼快照。安裝器先核對 SHA-256，再編譯到本資料夾。歷史相依標頭差異已記錄，並以實際水面重現核對。
- `reference/`：小型既有結果與來源；`data/`：有引文的 Test 4 表格抄錄。沒有論文 PDF、私人路徑或研究歷程大檔。
- `runs/`、`.tools/`、`.venv/`：本機生成，不納入發行或 Git。

以 `scripts/build_release.py` 產生新的獨立目錄及 ZIP：

```bash
.venv/bin/python scripts/build_release.py --output ../gc1991-release
```

輸出目錄必須尚不存在，以保留舊發行；其中包含 `gc1991-lab/`、`gc1991-lab-v1.zip` 與 ZIP 指紋。每個發行都有 `CHECKSUMS.json`；可執行 `python scripts/verify_files.py` 核對配送檔案是否完整。學生修改繪圖程式後指紋會變，這是預期現象，不等同數值失敗。

## 本機驗證與尚待工作

本機操作結果記錄在 [verification.md](verification.md)。上傳 GitHub 前仍需決定公開／私人 repository、名稱，以及原創程式／文件採用的授權條款；同時遵守 Basilisk 既有 GPL 條款。此版沒有替教師自動授予尚未指定的原創授權。

建議以一台 Windows／WSL 學生電腦走完安裝與 Notebook；本機 macOS 通過不等同 WSL 已測試。這項平台驗證不需要新增水理模型或更精細計算。

未來 GitHub 首頁直接顯示根目錄 README；連結採相對路徑，下載 ZIP 即可離線閱讀，不需要另建網站服務。若日後需要 GitHub Pages，可在發行流程確定後再加入。
