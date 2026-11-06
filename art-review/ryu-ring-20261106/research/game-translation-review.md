# 圓環砲・獨立動漫轉譯複核

日期：2026-11-06。結論：**本次新增技能的核心語意通過；不宣稱逐幀還原。**

## 實際檢視的產物

- 參考：`official-pv-27s.png` 與 `official-pv-ring-context.png`（官方 PV 公開 storyboard 取樣，來源見 `provenance.json`）。
- 遊戲：`../qa/presentation/mobile360-rank1-q0-{windup,growing,full,late,recovered}.png`；`mobile360-rank5-q4-full.png`；桌機 `desktop1280-rank1-q0-growing.png`、`desktop1280-rank5-q4-full.png`、`desktop1280-rank1-q0-recovered.png`；390 寬 `mobile390-rank5-q4-{growing,full,late,recovered}.png`。上述檔案由整合作者確認為加入移動亮端後的第三輪產物。
- 另用本機 ffmpeg 解碼當輪 `mobile360-rank5-q4-native-ring.webm`，4 fps 擷取18張，直接檢視 `native-ring-time-samples.jpg`。圖板為方便閱讀而裁出畫面 y=220..620 再縮放，不改動畫內容。這是影片取樣複核，並非聲稱播放／聽評完整影片。
- `../qa/presentation/report.json` 的 `sourceHashes` 與 `sourceHashesAfter` 一致，且七個 runtime 實檔 SHA256 一致；報告 `ok:true`、`errors:[]`。其中 `.omx/jujutsu-vfx.js` 為 `09bd0a7a126a0584f8d051a63fc076396bc4753728edee69143bc389b40afc00`，`.omx/jjk-ryu.js` 為 `1b14a13e77c59557346fd219c846a293fb4721481600de84331d8f47d3d80ca7`。

## 具體判斷

1. **出砲與成環可辨。** rank1 growing 與高階 growing 都先出現由人物額前側連出的彎管，末端仍有缺口；full 才閉合包圍身體。不是石流本體旋轉一條直砲，也不是第一張便憑空閃出完整魔法圈。人物頭砲／裸胸／毛領身份保留。
2. **圓環有砲束厚度。** 白核與青色外層形成粗厚連續砲道，中央人物可見，環內空腔保留地面與移動空間。相比官方 PV 斜俯視的多重橢圓弧，本作採遊戲世界平面的一個正圓；這是清楚的俯視改編，不應稱構圖完全相同。
3. **後續有沿環前進的亮端。** 360 寬原生影片約0.25秒可見成環中的開口；約0.5秒已閉合；接續取樣的白色壓力亮端出現在環的不同位置。這使持續砲束仍讀成能量沿彎砲道推進。rank5q4 full 與 late 的亮端位置也不同，不靠角色轉身冒充圓環。
4. **收束結束。** 360 寬原生影片約3.75秒後圓環已消失，人物仍在；rank1 與390寬 recovered 亦無殘環。收束是直接移除，沒有長尾退光；這不妨礙本次「彎砲成環」語意，但不能宣稱還原原片收勢。
5. **強化差異看得見。** rank5q4 相對 rank1 圓環更寬、更厚、維持更多輪；手機360與390的環均完整落在所測視窗內，人物及底部按鈕仍可辨。此處為受控高配呈現，不是自然養成或真手機效能證據。

## 程式佐證與邊界

`ringPath` 先沿額前朝向生成連接段，再以逐步展開的圓弧閉合；碰撞讀同一份 `segments`，閉合後取消內側連接段。VFX 畫同一路徑並加移動壓力亮端。因此核心幾何支持看到的彎曲砲束，不以滿圓AOE冒充環道。命中精度、牆體、回呼取消與生命週期完整性由戰鬥測試負責，本文件不以畫面代替其驗證。

官方取樣仍未證明精確方向、圈數、時長、半徑、跟身及每輪傷害；本作4–16輪、選卡增益與自動施放皆為遊戲改編。「円環式」取自媒體描述，不冒稱劇中正式招名。未聽評音效；視覺語意通過也不代表已替玩家證明主觀爽感。
