# 從基本水理到數值計算：三種水躍方法

本章以 **GC1991 水平矩形渠道 Test 4** 為共同問題，說明方程為什麼這樣寫、如何求解，以及計算結果可以如何解讀。不需要先學 C，也不必先讀原論文；先備知識是微積分、質量守恆、動量守恆與基本 Python。

**閱讀順序：**先讀符號與 standard-step，理解穩態的急流／緩流分支，再讀 Saint-Venant 的時間演進，最後理解 Boussinesq 壓力修正與教材自訂算法。文中的推導是教學整理；實際算法以隨附程式與固定原始碼快照為準。

本次為 **2026-09-15 方法文件擴充版**，計算核心、Test 4 輸入及既有數值參考值均未改動。

## 本章導覽

- [1. 共同問題、符號與假設](#notation)
- [2. 摩阻、比能與比力](#hydraulics)
- [3. Standard-step：從能量方程到水躍定位](#standard-step)
- [4. Saint-Venant：守恆律與有限體積計算](#saint-venant)
- [5. Boussinesq：垂向加速度如何修正壓力](#boussinesq)
- [6. 自訂 M92：實際離散與人工輸運](#custom)
- [7. 邊界、初始條件與時間平均](#conditions)
- [8. 結果、誤差與適用限制](#interpretation)
- [9. 從公式找到程式](#code-map)
- [10. 自我檢核與參考解答](#questions)
- [11. 來源與延伸閱讀](#references)

<a id="notation"></a>

## 1. 共同問題、符號與假設

### 1.1 這次實驗要解決什麼？

水由左往右流過固定寬度、水平底床的水槽。入口是淺水急流，出口給定較大的尾水深。問題是：**在這些條件下，水深沿程如何改變，水躍會出現在哪裡？**

三種方法的共同物理問題相同，但求解對象不同：

| 方法 | 主要未知量 | 如何形成水躍 | 本例能描述的範圍 |
|---|---|---|---|
| Python standard-step | 穩態水深 $h(x)$ | 急、緩流分支以比力匹配，接成零長度突跳 | 水躍位置與前後水深，不描述內部形狀 |
| Basilisk Saint-Venant（SV） | 隨時間改變的水深與單寬流量 $h(x,t),q(x,t)$ | 守恆通量在時間演進中捕捉水深突變 | 深度平均流動，突變寬度受數值離散影響 |
| 自訂穩態 B 修正（M92） | 節點上的 $h(x,t),q(x,t)$ | 修正動量通量，配合人工輸運求取穩態近似 | 固定設定的教學水面比較，未驗證滾流及局部流速 |

主專題將研究坡度轉折；**這個入門案例尚無坡度轉折**。以下偶爾保留底坡項，只為說明方程的一般意義，不能據此認為目前程式已支援任意底床。

### 1.2 符號表

| 符號 | 定義 | SI 單位 |
|---|---|---|
| $x,t$ | 向下游為正的座標、時間 | m、s |
| $z_b,h,\eta=z_b+h$ | 底床高程、水深、水面高程 | m |
| $B,A=Bh,P=B+2h$ | 渠寬、過水面積、濕周 | m、m²、m |
| $R=A/P$ | 水力半徑，不能與水深混用 | m |
| $u$ | 斷面平均流速；垂向推導中為領先階的水平流速 | m/s |
| $Q,q=Q/B=hu$ | 總流量、每單位渠寬流量 | m³/s、m²/s |
| $g,n$ | 重力加速度、Manning 糙率 | m/s²、s/m^(1/3) |
| $S_0=-dz_b/dx,S_f$ | 底坡、摩阻坡降 | 無因次 |
| $E,H=z_b+E$ | 比能、總水頭 | m |
| $M$（水理公式中） | 每單位渠寬比力 | m² |
| $\alpha,\beta$ | 能量、動量修正係數，本教材均取 1 | 無因次 |
| $B_c,\widehat B_k$ | 節點壓力修正、面上的壓力修正通量 | m³/s² |
| $\mathcal D$ | Boussinesq 速度導數組合 | 1/s² |

**同字母的不同用途：**程式的 `M=92` 是網格間隔數，與比力 $M(h)$ 不同；渠道寬度 $B=0.46$ m 與修正量 $B_c$ 不同。GC1991 原文用 $E$ 表示速度導數組合，本章改寫為 $\mathcal D$，避免與比能 $E$ 混淆。

### 1.3 固定案例與採用假設

三種方法讀取同一份 [`cases/test4.json`](../cases/test4.json)：

| 量 | 本案例設定 |
|---|---|
| 計算區域 | $x_{\rm in}=0.305$ m 至 $x_{\rm out}=14.0$ m |
| 渠道底床、寬度 | $z_b=0$，$B=0.46$ m |
| 入口水深、流速 | $h_{\rm in}=0.043$ m，$u_{\rm in}=2.737$ m/s |
| 尾水邊界 | $h_{\rm out}=0.222$ m |
| 流量 | $q=0.117691$ m²/s，$Q=0.05413786$ m³/s |
| 重力、糙率 | $g=9.81$ m/s²，$n=0.008$ s/m^(1/3) |
| 入口 Froude 數 | 由這組輸入算得 $Fr_{\rm in}\approx4.214$；原文報告 4.23 |

原文報告的糙率範圍是 0.008–0.011，但未確認 Test 4 的個別 $n$；14 m 為水槽全長，原文計算出口的位置亦未完全確認。因此，$n=0.008$ 與 $x_{\rm out}=14$ m 是**明列的教材採用假設**。尾水 0.222 m 是邊界輸入，不是最後一個量測站的 0.223 m。

三種方法都採不可壓縮、定密度、固定矩形斷面、無側向入流及深度平均的描述。沒有求解空氣夾帶、垂向滾流或紊流輸運方程。standard-step 與 SV 採靜水壓；B 修正的來源則在第 5 節推導。

<a id="hydraulics"></a>

## 2. 摩阻、比能與比力

### 2.1 Manning 摩阻

對本例向下游的正流，Manning 公式及其反解為

$$
Q=\frac{1}{n}AR^{2/3}\sqrt{S_f},\qquad
S_f=\left(\frac{nQ}{AR^{2/3}}\right)^2
=\frac{n^2u^2}{R^{4/3}},\qquad
R=\frac{Bh}{B+2h}.
$$

這裡的 $S_f$ 是能量線因摩阻而降低的坡降，不是底坡。即使水平底床 $S_0=0$，只要有流動與阻力，仍可有 $S_f>0$。

非定常動量式使用帶方向的寫法 $S_f=n^2u|u|/R^{4/3}$，讓摩阻永遠抵抗流速；在本例 $u>0$ 時，兩種寫法相同。以單寬流量表示，摩阻源項是

$$
s_q=-ghS_f=-\frac{gn^2q|q|}{hR^{4/3}}.
$$

三種程式都使用**完整矩形水力半徑**。只有在 $B\gg h$ 時才可近似 $R\approx h$；不能只在其中一種方法採寬渠道近似，再將差異都歸因於求解器。$n$ 表示渠道阻力；它不是水躍內全部耗能的替代參數。

### 2.2 比能與臨界水深

一般總水頭為 $H=z_b+h+\alpha u^2/(2g)$。$\alpha$ 修正斷面流速分布對動能通量的影響；本教材取 $\alpha=1$，所以

$$
E(h)=h+\frac{q^2}{2gh^2},\qquad
H=z_b+E,\qquad
Fr=\frac{u}{\sqrt{gh}}=\frac{q}{\sqrt{gh^3}}.
$$

固定 $q$ 對 $h$ 微分可得

$$
\frac{dE}{dh}=1-\frac{q^2}{gh^3}=1-Fr^2,\qquad
h_c=\left(\frac{q^2}{g}\right)^{1/3},\qquad
E_{\min}=\frac{3}{2}h_c.
$$

$h<h_c$ 是急流分支，$h>h_c$ 是緩流分支。在同一個大於最小值的比能下，通常有一淺一深兩個水深根。因此「解出一個正水深」還不夠，必須確保它在指定分支。本例 $h_c\approx0.112186$ m，入口 0.043 m 在急流側，出口 0.222 m 在緩流側。

### 2.3 比力與能量的差別

矩形斷面的靜水壓合力為 $\rho gBh^2/2$，動量通量為 $\rho\beta Q u$。兩者除以 $\rho g$ 得到總斷面比力，再除以渠寬 $B$，在 $\beta=1$ 下得到

$$
SF=\frac{Q^2}{gA}+A\frac{h}{2},\qquad
M=\frac{SF}{B}=\frac{q^2}{gh}+\frac{h^2}{2}.
$$

$SF$ 的單位是 m³，$M$ 的單位是 m²；本教材 `force()` 回傳後者。$M$ 本身不是力，也不是能量。把它乘上 $\rho gB$ 才得到此斷面的動量通量與壓力合力之和。

水躍通常使機械能降低。若以很短的水平控制體包住理想化水躍，忽略體內底坡力及壁面摩阻積分，便可用前後比力相等來匹配，而不能同時要求前後比能相等。

<a id="standard-step"></a>

## 3. Standard-step：從能量方程到水躍定位

### 3.1 先解水躍兩側的漸變流

令 $i$ 位於上游、$i+1$ 位於下游，$\Delta x=x_{i+1}-x_i>0$。相鄰斷面的穩態能量式是

$$
H_i-H_{i+1}=h_{f,i\to i+1},\qquad
h_{f,i\to i+1}\approx\frac{\Delta x}{2}
\left[S_f(h_i)+S_f(h_{i+1})\right].
$$

右側以兩端摩阻坡降的平均值近似沿程積分。一般工程模式還可能加入收縮／擴張損失；本教材的等寬水平直槽只保留以上摩阻項。HEC-RAS 也以逐斷面的能量平衡作為 standard-step 的基礎，但其完整幾何、損失選項與求解程序比這份教學程式更廣。[參考：HEC-RAS 能量方程說明](https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.0/theoretical-basis-for-one-dimensional-and-two-dimensional-hydrodynamic-calculations/1d-steady-flow-water-surface-profiles/equations-for-basic-profile-calculations)。

對固定 $q$ 的連續漸變流水面，$dH/dx=-S_f$，所以

$$
-S_0+(1-Fr^2)\frac{dh}{dx}=-S_f,
\qquad
\frac{dh}{dx}=\frac{S_0-S_f}{1-Fr^2}.
$$

水平渠道中，急流的 $1-Fr^2<0$，故水深沿下游增加；緩流的 $1-Fr^2>0$，故水深沿下游減少。這說明本例兩條分支的基本趨勢。當 $Fr\to1$，漸變流式的分母趨近零，不能靠跨過臨界點把它當成水躍內部方程。

**standard-step 與 direct-step 的區別：**前者先給定斷面距離 $\Delta x$，反解下一個水深；後者先選兩個水深，再從能量式反算距離。本程式使用前者。

### 3.2 每一步到底解什麼？

對已知急流水深 $h_i$，往下游求 $y=h_{i+1}$，解殘差

$$
r_s(y)=E(h_i)-E(y)
-\frac{\Delta x}{2}\left[S_f(h_i)+S_f(y)\right]=0.
$$

程式以二分法在 $h_i\leq y\leq h_c$ 內找根。若到臨界水深仍無可接受的根，便停止急流分支；不將結果延伸到緩流根。

對已知下游緩流水深 $h_{i+1}$，往上游求 $y=h_i$，解

$$
r_b(y)=E(y)-E(h_{i+1})
-\frac{\Delta x}{2}\left[S_f(y)+S_f(h_{i+1})\right]=0.
$$

本例上游緩流水深比已知下游水深大。程式先取 $[h_{i+1},2h_{i+1}]$，必要時放大上界，直到殘差異號，再二分求根。兩式中的 $\Delta x$ 都是正的斷面距離；差別在於哪個斷面是未知量，而非任意改變摩阻符號。

二分法只需連續殘差與異號括區：每次取中點，保留仍異號的半區間。本程式最多做 80 次迭代，水深括區寬度的停止容差為 $10^{-13}$ m。這是代數求根精度，不是水面預測對實驗的精度。

### 3.3 為什麼從兩端各算一條分支？

急流的兩個淺水特徵速度 $u\pm\sqrt{gh}$ 都指向下游，因此由入口條件建立急流分支。緩流有一個特徵方向指向上游，尾水可以向上游控制水面，因此由出口往上游建立緩流分支。

對本案例，兩分支在各自延伸範圍中都是候選漸變流水面；它們不是同時存在的兩層水。真正組合採用水躍前的急流分支與水躍後的緩流分支。

### 3.4 用動量匹配水躍

在候選位置 $x$ 取兩分支水深 $h_s(x)$ 與 $h_b(x)$，定義

$$
r_M(x)=M[h_s(x)]-M[h_b(x)].
$$

搜尋相鄰斷面間的 $r_M$ 異號。若 $r_{M,i}$ 與 $r_{M,i+1}$ 異號，以線性內插求

$$
x_J=x_i+\Delta x\,
\frac{r_{M,i}}{r_{M,i}-r_{M,i+1}}.
$$

再於 $x_J$ 內插兩分支的水深。`solve()` 採第一個找到的異號區間；若沒有匹配點，`jump` 為空。這是本固定案例的定位程序，並非任意渠道多重水躍的選解理論。[HEC-RAS 的動量方程說明](https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.4/theoretical-basis-for-one-dimensional-and-two-dimensional-hydrodynamic-calculations/1d-steady-flow-water-surface-profiles/applications-of-the-momentum-equation)亦說明水躍需要動量處理；本章斷面編號固定以上游到下游為序，閱讀其他手冊時須核對編號慣例。

令水躍緊鄰上、下游的水深為 $h_1,h_2$。由 $M(h_1)=M(h_2)$ 並排除沒有水躍的 $h_1=h_2$，可化為

$$
\frac{q^2}{g}=\frac{h_1h_2(h_1+h_2)}{2}.
$$

令 $r=h_2/h_1$，便有 $r^2+r-2Fr_1^2=0$。取正的深水根，即 Bélanger 關係：

$$
\frac{h_2}{h_1}=\frac{\sqrt{1+8Fr_1^2}-1}{2},
\qquad Fr_1=\frac{q}{\sqrt{gh_1^3}}.
$$

將上式代入前後比能差，可得古典水平矩形水躍損失

$$
\Delta E_B=E(h_1)-E(h_2)
=\frac{(h_2-h_1)^3}{4h_1h_2}>0.
$$

因此，水躍位置有**能量損失**；若用能量式連接其前後狀態，必須明列這項水躍損失，不能只保留漸變流的沿程摩阻。這裡的 $h_1$ 是水躍前的局部水深，通常不等於入口水深；$h_2$ 也通常不等於下游邊界水深。

### 3.5 可核對的 Test 4 計算例

以下數字由本教材函式計算，四捨五入僅供閱讀。

| 計算量 | 結果 | 解讀 |
|---|---|---|
| 入口水力半徑 $R_{\rm in}$ | 0.0362271 m | 小於入口水深 0.043 m |
| 入口摩阻坡降 $S_{f,\rm in}$ | 0.0399961 | 水平底床不代表摩阻為零 |
| 入口比能 $E_{\rm in}$ | 0.424813 m | 主要由速度水頭構成 |
| 入口比力 $M_{\rm in}$ | 0.0337604 m² | 為每單位渠寬量 |
| 入口往下游走 0.005 m 的水深 | 0.043011933 m | 急流在摩阻作用下增深 |
| 同一步的水頭損失 | 0.000199894 m | 約等於 $0.005\times0.04$ m |
| 匹配位置 $x_J$ | 1.458177 m | 相對本例原始 $x$ 座標 |
| 水躍前局部 $h_1,Fr_1$ | 0.0457584 m、3.83887 | 不等於入口值 |
| 水躍後局部 $h_2$ | 0.226593 m | 不等於尾水 0.222 m |
| 水躍比能損失 | 0.142583 m | 不包含水躍外兩段的摩阻損失 |

若直接以入口水深 0.043 m 代入共軛公式，得到約 0.235665 m；這只是「假想水躍緊接入口」的共軛深，不能替代沿程分支匹配。採水深內插後，比力相等還有極小的內插殘差；本例相對殘差約 $1.59\times10^{-8}$。

在教材根目錄可用以下 Python 片段核對，無須啟動 Basilisk：

```python
from core import standard_step as ss

q = 0.043 * 2.737
print(ss.critical(q))
print(ss.step(0.043, q, 0.008, 0.46, 0.005, "super"))
solution = ss.solve(q, 0.043, 0.222, 0.008,
                    width=0.46, x0=0.305, xout=14.0, dx=0.005)
print(solution["jump"])
```

### 3.6 算法總覽

```text
讀取共同水理條件，算 q 與臨界水深 hc
從入口沿下游建立急流分支，遇到無根就停止
從出口沿上游建立緩流分支
在共同座標比較兩分支比力，尋找第一個異號區間
內插水躍位置、前後水深，計算比能損失
輸出水躍前急流 + 水躍後緩流，保留同一 x 的兩個水深
```

本法預設水躍長度為零，沒有滾流區的空間結構。它能提供一個透明的穩態工程基準，但不能用其突跳線形去宣稱水躍長度為物理上的零。

<a id="saint-venant"></a>

## 4. Saint-Venant：守恆律與有限體積計算

### 4.1 從控制體寫出方程

對長度 $dx$、單位渠寬的水體，水量為 $h\,dx$。水量增加率等於流入減流出，故

$$
\frac{\partial h}{\partial t}+\frac{\partial q}{\partial x}=0.
$$

水平動量每單位長度、單位渠寬、除以密度後為 $hu=q$。通過斷面的對流動量通量為 $hu^2=q^2/h$；靜水壓合力除以密度後為 $gh^2/2$。加上底坡與摩阻，得到

$$
\frac{\partial q}{\partial t}
+\frac{\partial}{\partial x}\left(\frac{q^2}{h}+\frac{gh^2}{2}\right)
=gh(S_0-S_f).
$$

本例 $S_0=0$，右側就是第 2 節的 $s_q$。寫成向量形式：

$$
\mathbf U=\begin{pmatrix}h\\q\end{pmatrix},\qquad
\mathbf F(\mathbf U)=\begin{pmatrix}q\\q^2/h+gh^2/2\end{pmatrix},\qquad
\partial_t\mathbf U+\partial_x\mathbf F
=\begin{pmatrix}0\\s_q\end{pmatrix}.
$$

兩條式子分別守恆水量與水平動量。SV 假設垂向加速度對壓力的影響可忽略，所以壓力隨深度呈線性；它不含獨立的垂向流速或滾流變量。

### 4.2 為什麼它可以形成突跳？

若突變以速度 $s$ 移動，守恆律在極短控制體上給出 Rankine–Hugoniot 條件

$$
s[\mathbf U]=[\mathbf F],
$$

其中 $[\cdot]$ 表示下游值減上游值；有限的摩阻源項在控制體長度趨零時積分趨零。對靜止水躍 $s=0$，得到 $q_1=q_2$ 及動量通量相等，也就是古典比力匹配。

守恆式允許不連續的弱解；再選擇符合機械能耗散方向的解。數值通量讓突變在有限個網格內被捕捉，而不是逐格解析實際滾流。因此 SV 可以描述前後狀態與突變移動，卻不因圖上出現過渡寬度就取得物理水躍長度。

### 4.3 空間離散：有限體積與重建

每個格心儲存一個水柱狀態，面通量決定它與鄰格之間的交換。水平等寬網格的半離散式是

$$
\frac{d\mathbf U_j}{dt}=
-\frac{\widehat{\mathbf F}_{j+1/2}-\widehat{\mathbf F}_{j-1/2}}{\Delta x}
+\mathbf S_j\equiv\mathcal L(\mathbf U)_j.
$$

「共用面通量」的意思是相鄰兩格使用同一個面通量，只是正負號相反；加總全部格子時，內部交換恰好抵消。

本教材的 Basilisk 核心先對 $h,u,\eta$ 作受限線性重建。以平底上的任一變量 $v$ 為例，

$$
v_L=v_j+\frac{\Delta x}{2}\sigma_j,\qquad
v_R=v_{j+1}-\frac{\Delta x}{2}\sigma_{j+1},
$$

$$
\sigma_j=\operatorname{minmod}\left(
\theta\frac{v_j-v_{j-1}}{\Delta x},
\frac{v_{j+1}-v_{j-1}}{2\Delta x},
\theta\frac{v_{j+1}-v_j}{\Delta x}\right),\qquad \theta=1.3.
$$

`minmod` 在各參數同號時取絕對值最小者；若不同號或有零則取零。它限制陡變附近的斜率，避免直接用高階內插產生新的極值。固定快照的 `minmod2` 實作採上述形式。原生核心也包含靜水重建；本教材平底且保持濕潤時，它退化為相應的平底面狀態。[官方核心說明](https://basilisk.fr/src/saint-venant.h)。

### 4.4 面通量：Kurganov central-upwind

由左右重建值求 $q_L=h_Lu_L$、$q_R=h_Ru_R$、$c_L=\sqrt{gh_L}$、$c_R=\sqrt{gh_R}$，定義

$$
a^+=\max(0,u_L+c_L,u_R+c_R),\qquad
a^-=\min(0,u_L-c_L,u_R-c_R).
$$

當 $a^+-a^->0$ 時，面通量為

$$
\widehat{\mathbf F}=
\frac{a^+\mathbf F(\mathbf U_L)-a^-\mathbf F(\mathbf U_R)
+a^+a^-(\mathbf U_R-\mathbf U_L)}{a^+-a^-}.
$$

分子前兩項傳送物理通量，最後一項提供與波速及左右狀態差有關的數值穩定作用。這是隨附 `riemann.h` 中 `kurganov()` 的向量表示；不是呼叫精確 Riemann 解，也不是第 6 節自訂模式的 Rusanov 通量。[官方通量原始碼](https://basilisk.fr/src/riemann.h)。

### 4.5 時間推進與摩阻

目前的 SV 使用**顯式中點法**，以守恆狀態表示為

$$
\mathbf U^{n+1/2}=\mathbf U^n+\frac{\Delta t}{2}\mathcal L(\mathbf U^n),
\qquad
\mathbf U^{n+1}=\mathbf U^n+\Delta t\,\mathcal L(\mathbf U^{n+1/2}).
$$

先走半步估計中點狀態，再用中點的通量與源項走完整一步。Basilisk 欄位雖儲存 $h,u$，`advance_saint_venant()` 會先更新 $h$ 與 $hu$，再由新水深還原速度，並非把 $u$ 當守恆量直接相加。[官方時間積分原始碼](https://basilisk.fr/src/predictor-corrector.h)。

`update_checked()` 在兩階段都加入同一 Manning 動量源項。最後一步的全域收支使用實際中點通量與源項；若改用兩階段的算術平均，便會與這個 SV 方法的更新不一致。

主要時間步限制來自波速：$\Delta t$ 不超過各面 $\mathrm{CFL}\,\Delta x/\max(a^+,-a^-)$ 的最小值。入口到出口有 512 個格心控制體，$\Delta x\approx0.0267480$ m，CFL = 0.4。程式亦以顯式摩阻率限制時間步，並配合觀測／結束時刻縮短步長。CFL 限制是數值必要考量，不是「通過後即保證物理正確」的判準。

<a id="boussinesq"></a>

## 5. Boussinesq：垂向加速度如何修正壓力

### 5.1 這裡的 Boussinesq 指什麼？

本章指自由水面流動的**非靜水壓長波近似**，不是密度變化只保留在浮力項的另一種 Boussinesq 近似。它嘗試在深度平均方程中保留垂向加速度對壓力的領先階影響，仍沒有完整求解二維或三維紊流。

以下推導針對水平、不可穿透底床，以水平速度在水深方向近似均勻為起點。這是長波模型的閉合假設；在實際強烈滾流區，它不必成立。GC1991 的控制式與本節對應，見原文 p.1197，式 (1)–(4)。[原論文 DOI](https://doi.org/10.1061/%28ASCE%290733-9429%281991%29117%3A9%281195%29)。

### 5.2 從連續式得到垂向速度

用 $\zeta$ 表示自水平底床向上的垂向座標，$0\leq\zeta\leq h(x,t)$；以 $w$ 表示垂向速度。不可壓縮條件是

$$
\frac{\partial u}{\partial x}+\frac{\partial w}{\partial\zeta}=0.
$$

令領先階的 $u=u(x,t)$ 不隨 $\zeta$ 改變，並用底床不穿透條件 $w(0)=0$ 積分，得到

$$
w(x,\zeta,t)=-\zeta u_x.
$$

因此，即使水平速度近似均勻，水平的加速／減速仍會引起垂向運動。再將水面運動條件 $w(h)=h_t+u h_x$ 代入，便還原 $h_t+(hu)_x=0$，與前面的深度平均連續式一致。

### 5.3 垂向加速度與壓力分布

沿水粒子的垂向加速度為

$$
\frac{Dw}{Dt}=w_t+u w_x+w w_\zeta
=-\zeta\left(u_{xt}+u u_{xx}-u_x^2\right)
=-\zeta\mathcal D.
$$

三項分別代表水平速度梯度的時間變化、隨流動通過曲率場的作用，以及由垂向運動帶來的乘積項；它們都具有 $1/\mathrm{s}^2$ 的單位。這裡的 $u_{xt}$ 是混合偏導數，不是 $u_xu_t$。

忽略垂向黏性應力的領先階壓力推導，垂向動量式為 $Dw/Dt=-p_\zeta/\rho-g$。以水面表壓 $p(h)=0$ 積分，得到

$$
\frac{p(\zeta)}{\rho}
=g(h-\zeta)+\frac{\zeta^2-h^2}{2}\mathcal D.
$$

第一項是線性的靜水壓，第二項是非靜水壓二次分布。它的正負取決於流動導數，不一定增加壓力，也不一定造成耗能。

把壓力沿水深積分，得到斷面壓力通量

$$
\int_0^h\frac{p}{\rho}\,d\zeta
=\frac{gh^2}{2}-\frac{h^3}{3}\mathcal D.
$$

係數 $1/3$ 來自二次壓力分布的積分。定義

$$
B_c^{\rm full}=-\frac{h^3}{3}
\left(u_{xt}+u u_{xx}-u_x^2\right),
$$

就得到本章採用的完整非定常 Boussinesq 型平底控制式：

$$
\begin{aligned}
h_t+q_x&=0,\\
q_t+\partial_x\left(\frac{q^2}{h}+\frac{gh^2}{2}+B_c^{\rm full}\right)
&=-\frac{gn^2q|q|}{hR^{4/3}}.
\end{aligned}
$$

這個推導說明 GC1991 所列壓力項的由來，並不宣稱採均勻水平速度的假設可精確還原全部 Euler 流動。摩阻則是另外加入的工程閉合。檢查單位時，$h^3\mathcal D$ 為 m³/s²，正好與 $q^2/h$、$gh^2/2$ 同單位；它不能直接當成以公尺表示的水頭損失。

### 5.4 色散與耗散是兩件事

**色散**使不同波長以不同速度傳遞；**耗散**使機械能減少。Boussinesq 修正的主要角色是保留長波的非靜水壓／色散效應，它本身不是紊流耗能公式。

為看清此差別，暫取無摩阻、平底靜水 $h=h_0+\eta'$、$u=u'$，並只保留小擾動的一階項。完整方程化為

$$
\eta'_t+h_0u'_x=0,\qquad
u'_t+g\eta'_x-\frac{h_0^2}{3}u'_{xxt}=0.
$$

令擾動隨 $\exp[\mathrm i(kx-\omega t)]$ 改變，其中 $k$ 是波數、$\omega$ 是角頻率，可得

$$
\omega^2=\frac{gh_0k^2}{1+h_0^2k^2/3}.
$$

相速度 $\omega/k$ 隨波長改變，但此線性例子沒有給出振幅衰減率。當 $kh_0\ll1$，它回到淺水波速 $\sqrt{gh_0}$。這個關係只用來解釋**完整非定常式**的色散；不能拿來驗證下一節省略 $u_{xt}$ 的教材迭代器。

### 5.5 教材實際保留的是穩態 B 修正

GC1991 在向穩態迭代時省略 $u_{xt}$，理由是穩態時此項應為零（原文 p.1198）。教材自訂核心也保留此穩態近似：

$$
B_c^{\rm steady}=-\frac{h^3}{3}\left(u u_{xx}-u_x^2\right).
$$

$h_t,q_t$ 仍出現在迭代更新中，但那段過渡歷程不能直接視為完整非定常 Boussinesq 流動的真實暫態。尤其在上述靜水小擾動例子，穩態修正中的速度乘積是一階線性化會捨去的二階小量，無法重現完整式的同一色散關係。

若理想穩態連續式確實給出常數 $q$，則 $u=q/h$，可進一步改寫

$$
u_x=-\frac{q}{h^2}h_x,\qquad
u_{xx}=\frac{2q}{h^3}h_x^2-\frac{q}{h^2}h_{xx},
$$

$$
B_c^{\rm steady}=\frac{q^2}{3}
\left(h_{xx}-\frac{h_x^2}{h}\right).
$$

這顯示修正與水面曲率及坡度平方有關。**此式是連續、定常且定 $q$ 條件下的恆等改寫**；教材程式實際從局部 $u_j=q_j/h_j$ 求導，不強迫節點 $q_j$ 為常數，因此不能把兩種離散計算視為逐項相同。

### 5.6 B 修正何時消失？

若 $u$ 在空間與時間都均勻，所有導數為零，完整與穩態修正都消失。若只在某一時刻剛好 $u_x=u_{xx}=0$，仍未必有 $u_{xt}=0$。關閉穩態 B 開關時，自訂程式的**物理通量部分**回到靜水壓，但它的 Rusanov 通量、人工輸運、網格與邊界離散仍與原生 SV 不同，兩者不會因此成為同一個數值方法。

<a id="custom"></a>

## 6. 自訂 M92：實際離散與人工輸運

本節對照 [`core/custom_solver.c`](../core/custom_solver.c)。它使用 Basilisk 的網格與事件時鐘，再由自己的陣列求解；不是 Basilisk 原生 Green–Naghdi，也不是原論文 two-four 算法的完整逐項複製。

### 6.1 節點與控制體

本例有 92 個間隔、93 個節點，$j=0,\ldots,92$，

$$
x_j=x_{\rm in}+j\Delta x,\qquad
\Delta x=\frac{14-0.305}{92}\approx0.148859\ \mathrm m.
$$

每個內部節點對應寬度 $\Delta x$ 的控制體，兩端各為半寬 $\Delta x/2$。這樣總長度仍是 $14-0.305$ m，而不會多算兩端半格。面 $k$ 位於節點 $k-1$ 與 $k$ 之間；最外面的面直接位於入口及出口。

### 6.2 每個階段重新計算 B 項

在每一階段，先算 $u_j=q_j/h_j$。二階導數用中央差分，一階導數依階段使用前向／後向差分：

$$
(u_{xx})_j\approx\frac{u_{j+1}-2u_j+u_{j-1}}{\Delta x^2},\qquad
(u_x)^+_j\approx\frac{u_{j+1}-u_j}{\Delta x},\qquad
(u_x)^-_j\approx\frac{u_j-u_{j-1}}{\Delta x}.
$$

將其代入穩態 $B_c$ 式。預測階段面上的修正為 $\widehat B_k^+=(7B_{c,k}-B_{c,k+1})/6$；修正階段為 $\widehat B_k^-=(7B_{c,k-1}-B_{c,k-2})/6$。本設定只在 $4\leq k\leq M-2$ 的內部面啟用它，近邊界及外邊界的 B 面通量為零。

這種階段方向性與近邊界處理會影響結果。不能只說「有 Boussinesq 項」，而忽略它實際在哪些面、用哪種導數作用。

### 6.3 全域啟用的 Rusanov 通量

固定設定 `strip_mode=2` 使所有內部面使用 Rusanov 靜水壓通量。這裡「全域啟用」是指整個區域都使用它，**不是用同一個全域最大波速取代每面的局部波速**。每面的速度估計為

$$
a_k=\max\left(|u_{k-1}|+\sqrt{gh_{k-1}},\ |u_k|+\sqrt{gh_k}\right).
$$

用相鄰節點作左右狀態，先求

$$
\widehat{\mathbf F}^{\rm R}_k=
\frac{\mathbf F(\mathbf U_{k-1})+\mathbf F(\mathbf U_k)}{2}
-\frac{a_k}{2}(\mathbf U_k-\mathbf U_{k-1}).
$$

第二項是 Rusanov 自帶的數值耗散。程式還另外加入以下人工輸運；兩者不能混為同一項。

### 6.4 曲率感測器與額外人工輸運

水深曲率感測器為

$$
\xi_j=\frac{|h_{j+1}-2h_j+h_{j-1}|}
{|h_{j+1}|+2|h_j|+|h_{j-1}|}.
$$

平直或線性變化的正水深場有 $\xi_j=0$；急遽轉折時則可能變大。端點感測器設為零。在每個內部面，

$$
\varepsilon_k=\kappa a_k\max(\xi_{k-1},\xi_k),\qquad
\mathbf D_k=-\varepsilon_k(\mathbf U_k-\mathbf U_{k-1}),\qquad
\kappa=0.03.
$$

$\kappa$ 與 $\xi$ 無因次，$\varepsilon_k$ 的單位為 m/s。$\mathbf D_k$ 的兩個分量分別具有質量通量與動量通量的單位；它是面通量，不是每一步直接加到水深上的長度。

實際面通量組合為

$$
\widehat{\mathbf F}^{\pm}_k=
\widehat{\mathbf F}^{\rm R}_k
+\begin{pmatrix}0\\\widehat B_k^{\pm}\end{pmatrix}
+\mathbf D_k.
$$

因此即使 `boussinesq=0`，Rusanov 耗散與 $\mathbf D_k$ 仍存在。新增的 $\mathbf D_k$ 同時搬運水量與動量，並以通量差進入每一步的更新；它不是本教材對真實渦黏性或滾流耗能的校準模型。

### 6.5 兩階段更新、時間步與失敗檢查

令 $\ell_j$ 為節點控制體的實際寬度，定義

$$
\mathcal L^{\pm}(\mathbf U)_j=
-\frac{\widehat{\mathbf F}^{\pm}_{j+1}-\widehat{\mathbf F}^{\pm}_j}{\ell_j}
+\begin{pmatrix}0\\s_{q,j}\end{pmatrix}.
$$

固定 `source_mode=0` 採顯式摩阻，兩階段為

$$
\mathbf U^*=\mathbf U^n+\Delta t\,\mathcal L^+(\mathbf U^n),\qquad
\mathbf U^{n+1}=\frac{1}{2}\left[
\mathbf U^n+\mathbf U^*+\Delta t\,\mathcal L^-(\mathbf U^*)\right].
$$

這是全步預測再平均修正的形式，與第 4 節 SV 的半步中點預測不同；$\mathcal L^+$、$\mathcal L^-$ 的 B 導數也有階段方向性。不要從原論文的「two-four」名稱推論此改寫後方法在水躍區具有四階收斂。

本固定非週期網格的步長先估為

$$
a_{\rm est}=\max_j\left[
|u_j|+\sqrt{gh_j}+\frac{2h_j^2|u_j|}{3\Delta x^2}
\right],\qquad
\Delta t\leq\min\left(\frac{0.1\,\Delta x}{2a_{\rm est}},1\ \mathrm s\right).
$$

最後一項是 B 開啟時的顯式高階導數步長估計；分母的 2 反映端點半寬控制體。步長還會配合事件與結束時刻縮短。這是程式採用的保守估計，**不是完整非線性穩定性證明**。預測及修正階段均檢查正水深、有限值與異常大小；失敗時保存診斷並停止，不能把未完成的水面當成有效結果。

### 6.6 為什麼整體守恆，節點 q 卻仍可能不恆定？

把所有節點的質量更新乘上 $\ell_j$ 再加總，內部共用面通量會抵消，只剩入口減出口。因此整體水量可守恆。

但穩態離散質量式要求的是**總面質量通量**沿程一致。對本算法，該通量包含 Rusanov 與額外的人工輸運，並不等於某一個節點儲存的 $q_j$。在水躍內梯度很大時，數值輸運可以抵銷節點 $q_j$ 的空間變化。

所以「共用面通量守恆」與「局部 $q_j/h_j$ 可當作可靠的實驗平均流速」是兩個不同問題。本教材 M92 曾觀察到局部節點 $q$ 偏離入口約 45.6%，正是不能只憑全域收支通過來宣稱局部流速正確的原因。

<a id="conditions"></a>

## 7. 邊界、初始條件與時間平均

### 7.1 入口指定兩項，緩流出口指定一項

本例急流入口兩個特徵都進入計算區，所以指定 $h_{\rm in}$ 與 $u_{\rm in}$。緩流出口只有一項資訊由外部進入，故指定尾水 $h_{\rm out}$，另一項從域內相容關係估計。

SV 與自訂模式都直接施加入口面通量

$$
\widehat{\mathbf F}_{\rm in}=
\begin{pmatrix}
h_{\rm in}u_{\rm in}\\
h_{\rm in}u_{\rm in}^2+gh_{\rm in}^2/2
\end{pmatrix}.
$$

出口以內側當前階段的水深、速度 $h_i,u_i$ 估計

$$
u_b=u_i+2\left(\sqrt{gh_i}-\sqrt{gh_{\rm out}}\right),\qquad
q_b=h_{\rm out}u_b,
$$

$$
\widehat{\mathbf F}_{\rm out}=
\begin{pmatrix}q_b\\q_b^2/h_{\rm out}+gh_{\rm out}^2/2\end{pmatrix}.
$$

這來自無源項淺水特徵量 $u+2\sqrt{gh}$ 的相容關係。實作在邊界使用一階的局部近似，沒有完整追蹤特徵足點與沿程摩阻；不是 GC1991 原文出口式的逐字重現，也不是完整 Boussinesq 的精確無反射邊界。

**面上指定值與格點值要分清楚：**SV 的 ghost 條件供重建使用，最後真正進入守恆更新的是上述覆寫後的面通量。自訂模式連端點半格的 $h_j,q_j$ 都會更新，也沒有每步把端點水深強制重設為水庫值。因此輸出第一／最後節點的水深不必嚴格等於外部指定水深。

standard-step 沒有時間面通量，而是直接由入口、出口的水深建立兩條穩態分支。三種方法採相同的外部水理條件，但不能宣稱它們的邊界離散完全相同。

### 7.2 初始水面不是預先放好的水躍

兩個時間演進模式都從入口的急流漸變流水面出發，將

$$
\frac{dh}{dx}=\frac{S_f}{Fr^2-1}
$$

以四階 Runge–Kutta 積分到各採樣位置。`initial_rows()` 檢查水深始終為正且留在急流分支；不在某個位置預放擬合水躍。這條初始急流水面一般與出口尾水不相容，時間演進時由下游控制促成流況調整。

SV 載入格心 $(x,h,u)$；自訂模式載入節點 $(x,h,q)$。同一物理初始構想配合不同採樣位置，**不能把兩種 `initial.dat` 的第三欄直接互換**。

### 7.3 固定數值設定

| 方法 | 空間設定 | 時間設定 | 實驗比較使用的水深 |
|---|---|---|---|
| Standard-step | $\Delta x=0.005$ m | 穩態，無時間積分 | 匹配後的急／緩流分支 |
| SV | 512 格心，$\Delta x\approx0.026748$ m | 算至 1200 s，平均 1000–1200 s，CFL 0.4 | 時間平均水深 |
| Custom M92 | 92 間隔／93 節點，$\Delta x\approx0.148859$ m | 算至 300 s，平均 200–300 s，CFL 0.1 | 時間平均水深 |

SV 的 1200 s 是模擬時間，不是電腦必須計算 20 分鐘；實測計算耗時見[驗證紀錄](verification.md)。自訂模式的時間推進又帶有穩態迭代的解釋，不能以兩者「達到穩態的模擬秒數」直接比較實際水躍形成速度。

### 7.4 平均量與全域收支

時間平均水深定義為

$$
\overline h_j=\frac{1}{t_b-t_a}\int_{t_a}^{t_b}h_j(t)\,dt.
$$

程式使用每個實際時間步的舊／新水深線性內插，積分該步與平均窗的重疊區間。因此不是每秒快照的不加權平均，也不是最後一步的水面。標準差以同樣的時間積分計算 $\overline{h^2}-\overline h^{\,2}$。

令 $V=\sum_j h_j\ell_j$、$P_q=\sum_j q_j\ell_j$，離散收支應滿足

$$
V(t)-V(0)=\int_0^t\left(\widehat F_{h,\rm in}-\widehat F_{h,\rm out}\right)dt,
$$

$$
P_q(t)-P_q(0)=\int_0^t\left(
\widehat F_{q,\rm in}-\widehat F_{q,\rm out}+\sum_j s_{q,j}\ell_j
\right)dt.
$$

這裡 $V$ 為每單位渠寬水量，單位 m²；$P_q$ 單位 m³/s，乘上 $\rho B$ 才是整段實際水平動量。SV 用中點階段的時間衝量，自訂模式用兩階段平均的衝量，與各自更新一致。所有邊界量都取**實際採用的面通量**。

整體收支、正水深、完成指定時間和平均窗是檢查數值輸出的必要條件。若要主張穩態，還要查看前／後半平均、時間波動與流量趨勢，不能把「算到指定終止時間」直接當成穩態證明。

<a id="interpretation"></a>

## 8. 結果、誤差與適用限制

### 8.1 在哪裡與實驗比較？

實驗資料是 GC1991 Table 2 Test 4 的 14 個原始座標。$x=0.30$ m 位於本計算入口 0.305 m 之外：圖上保留叉號，但不納入誤差。其餘 13 點的 RMSE 為

$$
\mathrm{RMSE}=\sqrt{\frac{1}{13}\sum_{m=1}^{13}
\left[h_{\rm model}(x_m)-h_{\rm obs}(x_m)\right]^2}.
$$

SV 與自訂模式在相鄰格心／節點的平均水深之間作線性內插。standard-step 在水躍前用急流分支、水躍後用緩流分支；不把零長度突跳內插成一段人造斜坡。全部比較保留原始量測位置，不移動水面，也不調整座標來降低 RMSE。

### 8.2 如何解讀既有結果？

| 方法／控制 | 水深 RMSE | 此比較能說明什麼？ |
|---|---|---|
| Standard-step | 約 52.22 mm | 本組假設下的工程分支匹配與實驗有差距 |
| SV，512 格 | 約 52.20 mm | 此靜水壓深度平均計算的水面亦有較大差距 |
| Custom M92，B on | 約 14.14 mm | 固定設定的水面較接近這組實驗 |
| Custom M92，B off（既有教師控制） | 約 14.47 mm | 同格網下，B 項帶來的額外改善很小 |

不能把約 52 mm 降至約 14 mm 的全部差異歸因於非靜水壓：兩個模式的通量、網格、時間步及人工輸運同時不同。M184 曾得到約 26.12 mm，並比 M92 的水面中點位置 $x_{50}$ 改變約 9.17 cm；更細不一定更接近實驗，M92 的上升寬度尚未建立網格收斂。

這裡的 $x_{50}$ 是既有分析中的水面中間高度位置指標，不自動等於實驗水躍趾位置 $x_t$，也不等於 standard-step 的突跳位置 $x_J$。不同位置定義應分別標示，不能直接混用。

### 8.3 模型的能力邊界

- **Standard-step：**適合水躍兩側漸變流及理想化動量匹配；零長度假設沒有保留水躍內的有限長度坡度力、摩阻與複雜壓力分布。
- **SV：**能以守恆弱解捕捉突變；不求解垂向滾流、氣水混合或紊流結構，網格上的突變寬度不是物理滾流長度。
- **自訂 M92：**保留一種穩態非靜水壓修正，但水面上升受到人工輸運及所選網格影響，局部 $q/h$ 也有已知限制。它尚不是經普遍驗證的水躍流速或能量閉合模型。

已知強稀疏波測試與更細網格的失敗保留為限制，不因教學接受而改判通過。當前課堂不要求學生重跑這些教師研究矩陣，也不以任意加大 Manning $n$ 來掩蓋水躍耗散。

### 8.4 三個容易混淆的「通過」

| 名稱 | 所問的問題 | 本教材如何處理 |
|---|---|---|
| 安裝／數值重現 | 不同電腦是否得到同一組既有結果？ | C 水深差容許 0.2 mm；standard-step 位置差容許 2 mm |
| 離散守恆與完成狀態 | 程式是否完成、保持正水深，且收支符合自己的離散式？ | 每次實際執行檢查，失敗保留紀錄 |
| 實驗驗證與數值收斂 | 方程及離散在何範圍能可靠描述真實流動？ | 需獨立量測、解析度與不確定度評估；不由前兩項保證 |

`reproduction passed` 指第一項，不代表 RMSE 很小，也不代表自訂模式的局部流速已驗證。一般可用 $z_b+h+u^2/(2g)$ 作**靜水壓工程總水頭指標**；在 B 修正作用區，不能不加說明就把它當作完整非靜水壓機械能。用受數值輸運影響的局部 $q/h$ 計算水躍內能量，更需要小心解釋。

<a id="code-map"></a>

## 9. 從公式找到程式

| 本章內容 | 程式位置 | 閱讀重點 |
|---|---|---|
| 比能、比力、臨界與共軛深 | [`core/standard_step.py`](../core/standard_step.py)：`energy`、`force`、`critical`、`conjugate` | 公式可直接逐項對照 |
| 矩形摩阻、逐步求根 | 同檔：`friction`、`step`、`bisect` | 半徑、能量殘差、分支與括區 |
| 水躍匹配 | 同檔：`solve` | 比力異號、位置內插與兩分支輸出 |
| SV 重建與面通量 | [`core/sv_instrumented.h`](../core/sv_instrumented.h)：`update_saint_venant` | `kurganov` 呼叫、外邊界面通量 |
| SV 摩阻及時間收支 | [`core/sv_case.c`](../core/sv_case.c)：`update_checked`、`advance_checked` | 更新的是動量；中點階段收支 |
| 自訂 B 與人工輸運 | [`core/custom_solver.c`](../core/custom_solver.c)：`operator` | `bflux`、`b_face`、`sensor`、`dflux` |
| 自訂時間更新與檢查 | 同檔：`event advance`、`valid`、`sum_state` | 階段方向、半格權重、失敗狀態 |
| 初始條件、執行與 RMSE | [`lab.py`](../lab.py)：`initial_rows`、`run_method`、`_rmse` | 初始資料的欄位、輸出來源、原始量測座標 |

SV 的 `predictor-corrector.h`、`riemann.h` 與 `utils.h` 位於隨附固定 Basilisk 原始碼壓縮包內；安裝後可在本教材 `.tools/<識別碼>/basilisk/src/`（識別碼包含快照指紋、作業系統與架構） 對照閱讀。教材採用完整一致的快照，而不是任意混合目前網站上的標頭版本；來源指紋見 [`vendor/basilisk-source.json`](../vendor/basilisk-source.json)。若要讀更完整的函式導覽，見[程式導讀](code-guide.md)。

<a id="questions"></a>

## 10. 自我檢核與參考解答

先嘗試用公式回答，再查看下面的簡答。這些練習不用改 C 核心或重新跑參數矩陣。

1. 水平底床為什麼仍有摩阻損失？
2. 為什麼 standard-step 每一步要指定急流或緩流分支？
3. 為什麼不能直接拿入口水深套共軛公式，當成下游邊界水深？
4. Boussinesq 壓力項中的 $-h^3/3$ 從哪裡來？
5. 省略 $u_{xt}$ 後，能否用計算過程研究真實色散波的傳播速度？
6. 關掉 B 後，自訂模式是否就等於目前的 SV？
7. 為什麼 $q_j$ 不恆定，整體水量仍可能守恆？
8. RMSE 下降是否足以宣稱水躍長度與局部流速都更正確？

### 參考解答

1. $S_0$ 是底床幾何，$S_f$ 是摩阻坡降。水平底床不消除流動對壁面的摩阻；$dH/dx=-S_f$ 仍成立。
2. 同一比能常有淺、深兩個根。必須沿符合邊界控制的分支求根；程式不能跨越臨界水深來代替動量匹配。
3. 水躍前已有沿程摩阻，局部 $h_1$ 不等於入口值；水躍後到出口也有漸變流。共軛公式連接的是同一理想化水躍的兩側。
4. 垂向加速度使壓力多出 $(\zeta^2-h^2)\mathcal D/2$；在 $0\leq\zeta\leq h$ 積分便是 $-h^3\mathcal D/3$。
5. 不能直接如此解讀。完整非定常式與省略混合導數的穩態迭代器具有不同的暫態算子。
6. 不等於。Rusanov／Kurganov、人工輸運、網格、邊界處理與時間推進都仍有差異。
7. 守恆更新使用相鄰格共用的總面通量，包含數值輸運；它不等於單一節點 $q_j$。內部通量相消仍可使全域收支閉合。
8. 不足以。RMSE 只評估指定座標的水深；水躍長度、局部流速及紊流需要各自的量測與數值不確定度證據。

<a id="references"></a>

## 11. 來源與延伸閱讀

本章以原論文、官方方法文件及**本教材實際原始碼**交叉核對。公式推導與計算例由本教材重新整理，未重製原論文圖版或全文。

- **Gharangik, A. M. & Chaudhry, M. H. (1991).** Numerical simulation of hydraulic jump. *Journal of Hydraulic Engineering*, 117(9), 1195–1211. [DOI](https://doi.org/10.1061/%28ASCE%290733-9429%281991%29117%3A9%281195%29)。p.1197 式 (1)–(4) 為深度平均 Boussinesq 控制式；p.1198 說明省略混合時間／空間導數的穩態迭代；pp.1198–1199 說明原論文的 MacCormack 與 two-four。其算法不能與本教材後續改寫的自訂核心混稱。
- **USACE HEC-RAS Hydraulic Reference Manual.** [Equations for Basic Profile Calculations](https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.0/theoretical-basis-for-one-dimensional-and-two-dimensional-hydrodynamic-calculations/1d-steady-flow-water-surface-profiles/equations-for-basic-profile-calculations) 與 [Applications of the Momentum Equation](https://www.hec.usace.army.mil/confluence/rasdocs/ras1dtechref/6.4/theoretical-basis-for-one-dimensional-and-two-dimensional-hydrodynamic-calculations/1d-steady-flow-water-surface-profiles/applications-of-the-momentum-equation)。用於 standard-step 與動量處理的工程背景，不代表本教材已完成 HEC-RAS 驗證。
- **Basilisk 官方原始碼文件。** [saint-venant.h](https://basilisk.fr/src/saint-venant.h)、[riemann.h](https://basilisk.fr/src/riemann.h)、[predictor-corrector.h](https://basilisk.fr/src/predictor-corrector.h)。線上頁面提供閱讀入口；本教材實際使用的是 `vendor/` 所封存的 2026-09-08 快照與已記錄的局部邊界修改。
- **教材的證據與使用說明。** [本機驗證紀錄](verification.md)、[資料來源與授權](../THIRD_PARTY_NOTICES.md)、[操作指南](quickstart.md)。這些檔案分別回答如何重現、資料從何而來，以及如何完成第一次課堂操作。
