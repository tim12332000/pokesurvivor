# Freeze：經典 LF2 2.0a 考據與素材

本次採用原版 **Little Fighter 2 v2.0a**，不是 Remastered，也不是 R-LF2／LF2.5 的改招版。圖片由原始安裝包讀取，沒有 AI 重畫或換色角色。原作由 Marti Wong、Starsky Wong 製作；遊戲免費下載不等於素材開源，本專案程式授權不延伸涵蓋 LF2 原素材。

## 可重現來源

- [LF2 官方 FAQ](https://lf2.net/faq_en.html)：原版以 Visual C++／DirectX 製作，圖像由 Marti 繪製；官方沒有公開原引擎原始碼。
- [OpenLF2 原始碼](https://github.com/OpenLF2/OpenLF2)：MIT 授權的重實作，與原版作者無隸屬關係。其 `src/resources/installer.cpp` 提供原安裝包的唯讀資源結構；`dist/web/installer-store.js` 提供包的下載位置、大小與 SHA256。此次參照該格式撰寫 Python 提取器，沒有執行安裝程式、註冊表命令或工具列。
- 原包下載：[Internet Archive 保存的 LF2Setup.exe](https://archive.org/download/little-fighter-2_202404/Little%20Fighter%202.rar/Little%20Fighter%202%2FLF2Setup.exe)，29,586,263 bytes；SHA256 `540c485547e234b0d09595f54d067aafd7176092c308aca61868f3cbc03030e1`，與 OpenLF2 固定值完全相同。
- [原版檔案索引](https://www.lf-empire.de/downloads/other/LF2-files.php) 可作檔名交叉參考；本輪直接下載該頁遇到 403，實際素材來源是上述 SHA 固定的原包，沒有把搜尋摘要當成已下載原檔。

重建：把相符原包放在 `art-review/freeze/source/LF2Setup.exe`，執行 `python tools/build_freeze_assets.py`。只需工作區已有 Pillow；無新增依賴。原始大包、研究抓取 C++／HTML、解出的全套 WAV 不加入正式開局包。原始及 runtime SHA 保存於 `source-manifest.json` 和 `assets/lf2/freeze/manifest.json`。

原 BMP 使用 BI_RLE8，部分姿勢含 delta 指令；Pillow 的直接解碼會把 `_1`／`_2` 弄成幾條橫線，因此重建器用完整的 RLE8 delta 座標解碼，再將原 LF2 的純黑色鍵 `(0,0,0)` 轉 alpha。原遊戲不顯示的1px彩色圖格分隔列／行也轉透明，防止俯視鏡頭非整數縮放時滲出綠色矩形邊緣；圖格內其他像素值與原圖尺寸皆保留。獨立逐像素核對1,940,292個格內像素，完全相符。已實看修正後 `_0`、`_1` 的身體、手臂、披風與拳腳。`freeze_ice.png` 僅裁原 pic8／9 並保留原青色冰塊像素，去掉 Freeze 本人的色塊，作為實際受凍敵人之外覆層；不是把敵人換成 Freeze。

## 原作動作盤點與轉譯契約

直接檢查原包解密後的 `freeze.dat`、`freeze_ball.dat`、`freeze_column.dat`、`weapon7.dat`；metadata 保留每格 `pic/wait/next/centerx/centery/bpoint/wpoint/opoint/itr/bdy`。原模擬為30fps，一格實際停留 `(wait+1)/30` 秒。

| 原作能力 | 原版動作鏈與必要關係 | 本作轉譯 |
| --- | --- | --- |
| 冷凍波／Ice Blast | 身體235→236→237蓄波，238從手前 opoint 釋放，239→240收勢；原生 `.2s` 出波，總 `.467s`。飛行球有自己的動畫0→1→2→3→4→5；撞擊10→11→12→13。 | 自動朝敵方發射直線冰波，命中才給凍結；本體收勢後在途球繼續飛行。數量／距離／強度是生存遊戲改編。 |
| 冰霜拳／Icicle | 245→249俯身發力，250擊地 opoint，251→252起身；`.333s`擊地，總`.8s`。原 column action100→101→102→103依序生成三根冰柱，分別啟動60、50、0。 | 三根沿開放地面逐一冒起，使用原柱起勢與完整成形格；牆後不生柱。投入後柱數／覆蓋成長是改編。 |
| 冰鋒之劍／Summon Sword | 270→274抬手凝冰，275產生 weapon7 並以 wpoint接住，`.367s`出劍，總`.467s`。之後劍是持有物，不是每次攻擊重播召喚。20→21→22→23／25→26→27→28是兩套持劍揮擊，wpoint.weaponact選原劍格並以兩邊的手握點貼合，cover控制身前／身後。 | 初次學劍施放先召喚，之後保持持劍、接近才揮砍。weapon7 strength_list四種攻擊皆`effect:3`，即冰劍命中也會凍結；沒有虛構碎冰爆破被動。距離投資同步放大實際劍身，握手位置不漂移。 |
| 白色龍捲／Whirlwind | 260→264旋身蓄力，265釋出自己的冰旋風，266→268收勢；`.367s`釋出，總`.833s`。效果150→153開場，154→157循環，158→159散去。 | 原冰旋風貼地向前推進，真實多段命中及把普通敵人捲動／拉向旋風；身體能收勢、移動撤退，不整段黏在玩家腳下。本作沒有原版垂直拋飛／摔落系統；波次與數量成長是改編。 |
| 普通拳腳 | 空手60→61／65→66前伸拳；沒有持劍時能在近身空檔接拳。 | 作為空手近身保底，不取代冷凍波或發明新的原作技能。 |

未納入本角色：與 Firen 合體變 Firzen，需要另一角色及合體條件，本輪不是把 Firzen 的冰火招算在 Freeze 名下；跳躍、撿地上物件、投擲任意武器和完整 D/J/A 搓招輸入也沒有原樣移植。原兩向側身、頭髮、淺色披風、深藍服、實體冰劍與冰柱／白色龍捲保留；俯視地圖、自動施放、敵人抗性與成長卡屬 PokéSurvivor 改編。

## Runtime 圖格及介面

- `freeze_0/1/2.png`：79×79格，80px步距，原 pic0–69／70–139／140–209；實際第三張只有有效前三列，不能把 declared上限當成有畫的格數。
- `freeze_ball.png`：81×82格，82×83步距；`freeze_col.png`：109×109，110步距；`freeze_ww.png`：159×159，160步距；`weapon7.png`：69×69，70步距。
- 身體固定以原 `centerx/centery` 當腳底，不用每格 alpha 外框重新放大；原始站高基準65px，預設本作64px。倒下、蹲身因此自然縮短。
- `G.LF2Art` 提供 `load/loaded/ready/draw/drawEffects/sample/frame/sequence/pointFor`；所有戰鬥效果只讀 `G.LF2Freeze.renderStates().effects`，凍結圖層只讀 `frozenTargets()`；不在 draw 修改傷害、位置、lease或時計。
- 每張PNG/WAV URL帶runtime SHA，metadata URL採載入script的`data`hash；原WAV由獨立`G.LF2Audio`接到遊戲原生聲音bus。本輪程式／音訊實作檢查與實際聽評分開記。

## 當次已看與未看

已獨立看過 QA 的 `desktop-selection.png`、`desktop-normal-entry.png`、`mobile390-normal-entry.png`：原版髮型、披風、服裝及手中冰波辨識成立，腳底與地面陰影一致，390寬下主角及可走路面、觸控區仍可辨。首張選角圖名字重複已交回註冊作者修正；該舊圖不作新文案通過證據。

另已看過 `qa/natural-desktop`、`qa/natural-mobile390` 的準備／釋出／收勢及獨立效果截圖：普通冰波收勢後繼續飛行，召劍後原武器持有，三根原冰柱逐一成形，白色龍捲離開本體前進，角色及可走路面仍可辨。自然局與受控片分開：自然報告記錄桌機從Lv1真選卡到Lv9、四招命中；原生影像不是把靜圖拼成影片。舊自然片桌機結束前曾修改純美術的劍時序，故不把整份片稱為最終hash相同；QA用獨立 `blade-current` 片與原生左右命中格補驗現行20／25鏈，每段8/30秒，實際22／27接觸窗為4/30–6/30秒。

已實際以 ffmpeg seek並檢視 `blade-current/native-blade.webm` 的6、7、8秒格（持劍、凍結及回到待機），以及 `natural-desktop/native-growth.webm` 的50秒格（水平揮劍、真敵人冰封）。這只聲明看過取樣格，不冒稱完整聽評或逐格看完整影片。

最終純美術除分隔線後，已獨立看過 `qa/final-cycles/column-independent.png`、`lf2-iceball-release.png`、`whirlwind-fade.png`，以及實際從`native-cycles.webm` seek出的5、6、7、8秒格：原冰柱三段、冰劍、白色旋風、凍結外覆層成立，原先綠色矩形邊已消失。`qa/final-cycles-source.json`記錄`sourceStable:true`，其球圖SHA及manifest SHA與當前工作樹完全相符。視覺判定保存`.omx/state/freeze/ralph-progress.json`；沒有未解美術阻擋。影片及正常桌機／390寬證據不代表實體手機長局；聲音檔來自原包已核對，未對每份聲音做真人實聽評價。
