# Firzen／Julian：經典 LF2 2.0a 來源與動作合約

本輪使用經典 **Little Fighter 2 v2.0a**，不使用 Remastered、R-LF2 或 LF2.5 的改招素材。原圖、原音效與資料由 Marti Wong、Starsky Wong 製作；本專案程式授權不涵蓋原素材。人物直接加入選角與本作自動戰鬥，並非移植原版所有操作或引擎。

## 已實際核對的來源

- 原版安裝包沿用 Freeze 首發的 SHA 固定來源：`art-review/freeze/source/LF2Setup.exe`，29,586,263 bytes，SHA256 `540c485547e234b0d09595f54d067aafd7176092c308aca61868f3cbc03030e1`。從[保存的原包](https://archive.org/download/little-fighter-2_202404/Little%20Fighter%202.rar/Little%20Fighter%202%2FLF2Setup.exe)讀取；沒有執行安裝器。
- **原包的 `readme.txt`** 直接列出 Firzen 三招及 Julian 六招，名稱、輸入與角色歸屬不依賴搜尋摘要。原始檔保存本機 `art-review/lf2-bosses/source/readme.txt`，SHA 收錄兩位角色的 manifest。直接讀過 Firzen／Julian 對應段落。
- 原包的 `data/data.txt`、兩位角色 `.dat` 及其依賴物件完整解密後，保存原 `pic/wait/next/centerx/centery/opoint/wpoint/itr/bdy/hit_*`。每個物件 ID 由原 `data.txt` 對應，未憑檔名猜招式。
- 經典引擎有原 `.dat` 以外的特殊分派。本輪另實讀 [OpenLF2 的 object rules](https://github.com/OpenLF2/OpenLF2/blob/main/scripts/base/game/objects.lua) 的 `objects.update`，以及 [combat rules](https://github.com/OpenLF2/OpenLF2/blob/main/scripts/base/game/combat.lua) 的 `armored` 作交叉佐證。這是獨立重實作的原始碼，不冒稱原 LF2 官方引擎原始碼；讀取的副本留在本機 source 目錄。

重建命令：`python tools/build_lf2_boss_assets.py`。只使用工作區已有 Pillow，重用 Freeze 的安全原圖解碼及 `.dat` 解析函式，不修改既有 Freeze 產物。輸出 `assets/lf2/firzen/manifest.json`、`assets/lf2/julian/manifest.json` 與對應 PNG／WAV，另存本目錄兩份 source-manifest。原大包、原始研究碼與解密全文不放進正常開局包。

## 原始像素與圖格

原 BMP 有 BI_RLE8 delta 指令；沿用先前已修正的完整解碼器，避免一般解碼器把身體圖變成橫線。只將純黑色鍵及原遊戲忽略的 1px 彩色分隔行／列轉透明；不重畫、不換色、不重採樣圖格內容。獨立逐像素核對 **4,586,787** 個格內像素完全一致，並核對所有 runtime SHA，記於 `pixel-verification.json`。

metadata 保留原 `declaredEnd` 和實際 `physicalEnd`；繪製 `end` 不得超過下一張表的起始索引，避免 Firzen 第一張追蹤球的未用實體格搶到 `firzen_up` 的 pic8。Julian 骷髏表原宣告0–7，實體有0–11，source50鏈確實使用8–11，因此最後一張可用格按實體大小延伸。超出實體的 pic50 等原生控制框仍保持空白；不能用其他圖冒充缺少的可見動作。

Firzen 使用原79×79身體格，延伸炮姿勢為159×79；Julian 原身體多為79×99，跑擊格為109×99。固定原 `centerx/centery` 錨點，不能按每格外框重新放大蹲身／倒地姿勢。Firzen 的 `freeze_ice.png` 裁原 Freeze pic8／9，只保留原青色冰塊像素，以包住真正受凍敵人；不是把敵人改成 Freeze。

## Firzen：原包明列的三招

所有時間以 LF2 原30fps、每格 `(wait+1)/30` 秒計算。

| 原包名稱／輸入 | 身體與接觸來源 | 轉譯時不可丟掉的關係 |
| --- | --- | --- |
| Firzen Cannon／D→J | 身體265→269蓄力，270於10/30秒從手前生成 oid223 action0。271→272→273→271迴圈，272出 action2後續炮；首次後續於15/30秒，後續每4/30秒，原恢復280。 | 連續向前的冰火混合炮，由手／炮姿放出；原本可按住持續，有限自動炮串與成長輪數須明示為本作改編。不能改成無來源瞬間全圖傷害。 |
| Overwhelming Disaster／D↑A | 身體240→247總18/30秒；243於6/30秒出上方閃光，244於8/30秒生成上升 emitter50；emitter59在其12/30秒時以`hit_Fa:9`分裂，故原追蹤球約在整招20/30秒生成。 | 大球在頭頂上升並分成火／冰追蹤球，已釋放後獨立追敵。引擎選擇 fire221／ice222，普通遭遇至少4顆，依敵數增加至合計10顆；不是固定5火＋5冰。自動索敵、可重現的元素分配和成長上限屬改編。 |
| Arctic Volcano／D↑J | 身體249→260總44/30秒，258於17/30秒生成 oid221 action80；該框 `hit_Fa:11` 呼叫原引擎複合爆發。 | 中心原火爆炸＋周圍冰柱／地火，再接空中冰火追擊，是同一招的組成；不能只做六個換色圓圈當作全招。 |
| 普通近身拳腳 | 60→61／65→66總5/30秒，接觸2/30秒起；超重拳及跑擊另有原格。 | 空檔有本體近身迎擊，不將普通拳誤稱第四個原作特殊能力。 |

Volcano 的引擎交叉佐證具體為：中心 `firen_flame` action109；六個 `freeze_column` action100母柱（前後 x±80／±100、z±7及0），母柱又依次生成三個原冰柱；六個地火 action50；以及上方 `firzen_chasef` action81追擊 emitter。這是原合成招式的依賴盤點，並不強制本作複製原數值、友軍誤傷或原Z軸。需要縮減或改編時應明確交代，而不能當作原作沒有該組成。

## Julian：原包明列的完整六招

| 原包名稱／輸入 | 原身體鏈／時點 | 轉譯語意 |
| --- | --- | --- |
| Soul Punch／Run＋A | 300→305六格各1/30秒為肩拳接觸，306、307收勢，總14/30秒。 | 本體向前的實際衝拳與碰撞；不能站原地在遠處標一個傷害圈。 |
| Uppercut／D↑A | 235→86→87→88→89→79→0；86於2/30秒起、88於6/30秒起是兩個原攻擊窗。落回0前共22/30秒。 | 近身上勾拳，本體肢體接觸與收勢可辨；本作沒有完整原Z軸拋飛系統時應明示。 |
| Skull Blast／D→A | 260→276總33/30秒；261、264、268、271、274在4／9／16／21／26 tick各放一顆 oid228 action100。 | 真正連續五次出手。原 action100為引擎控制框，另產生可飛行骷髏 action0；可轉向追敵但不是無限制瞬移命中。 |
| Mirror Image／DJA | 106→103→104→105總22/30秒；103於2/30秒產生本體外觀 dummy240，後者為240→251非傷害影像。 | 迴避移動／誘導用影像，不是進攻分身。是否轉移敵方瞄準必須由真實目標分派證明，不用殘影就宣稱嘲諷。 |
| Big Bang／D↑J | 310→322總43/30秒；318於12/30秒發出 oid229 action40。 | 巨大的本體近身能量柱／爆發，不混成遠射 Soul Bomb。原效果40→51總19/30秒，前40–47有攻擊至14/30秒，最後散去。 |
| Soul Bomb／D→J | 280→291總20/30秒，289於12/30秒從手前發出 oid229 action0。 | 真正飛行的巨大能量球，飛行及撞擊爆炸分開；不能以瞬間線段冒充。原球 state3006、dvx18，傷害與爆炸為兩個接觸概念。 |

Julian 原 `frame0` 的 `hit_Fa/hit_Ua/hit_Fj/hit_Uj/hit_ja` 分別對應260／235／280／310／106；Soul Punch 是跑攻，故不在這五個方向輸入欄位。原盔甲反應另由引擎計時控制，獨立重實作可佐證其存在；未驗就不宣稱無條件無敵、固定三次免傷或永久反射。原兩向身體、假影及原球／能量柱輪廓要保留，任意武器拾取、原D/J/A搓招與完整物理仍屬移植界線。

本輪主代理已明確選擇 **四招正式學習＋一項近身基礎動作＋一項明示取捨**：Skull Blast、Uppercut、Soul Bomb、Big Bang 進技能池與四個圖示；Soul Punch 在玩家朝近敵移動、身體可出手時作真實接觸衝拳，不另占學招卡，空檔還有普通拳。Mirror Image 首發不接入，因本作尚未有手動迴避與真實誘餌瞄準分派；不以攻擊分身或裝飾殘影假稱完成此招。這是自動戰鬥首版的功能取捨，不宣稱原 Julian 只有四招。無條件盔甲免傷亦不附送。

## 目前證據界線

已核對：原包 SHA、原 readme 六／三招清單、所有列出的原 dat鏈、依賴物件／實體圖格範圍、原始細胞像素與 runtime SHA，以及 OpenLF2 特殊分派交叉佐證。

已獨立看過 `qa/firzen-desktop-normal-entry.png`、`qa/julian-desktop-normal-entry.png` 及 Julian 選角：Firzen 原綠髮、黃衣、披風與雙手冰火蓄能姿勢成立；Julian 原深色盔甲、面具紅眼、披風與掌中能量成立，身型比 Firzen 高大，腳底與地面陰影相接。四個 Julian 學習圖示符合上述取捨，不是把原六招盤點縮成四招的證據。

仍待候選完整 phase：來源考據者須獨立看桌機／手機原生出招片段，涵蓋首段／後段／收勢及真正消散，再填本節。此時未把起始截圖稱為全部技能、玩法或完整畫面已完成，也未宣稱聽過全部原 WAV。


### Firzen 當次自然局取樣

已獨立看 `qa/firzen/natural-desktop` 的炮釋放／收勢、上升母體、分裂追擊、火山冰柱／地火／中央火爆與收勢圖。能辨識原雙手合炮、金色連炮、分離的原火／冰追擊球、原冰柱三段與原火爆圖；火山高峰短暫遮住本體，收勢即重新看見原角色和周圍路面。另用真正 ffmpeg seek 取出並實看 `native-growth.webm` 的20、35、45秒格：移動、本體收勢後在途冰火球與炮仍運作，角色與怪群有正常相對位移。這些是實際原生影片取樣，不聲稱完整逐格播放或聽評。

此桌機自然片製作期間另修正母體 lift 的升空先後；該片證明自然選卡與各招整體身份，最終升空→分裂關係仍以後續來源穩定的手機／受控原生片定點補驗，不冒稱早期片與最終產品每個byte相同。Julian 各招與 Firzen 最終 lift 版本取樣仍待補齊。


### 最終候選考據／動作複核：通過

已獨立實看 Julian 自然桌機的骷髏逐發、上勾拳接觸與收勢、實體能量球、源300 Soul Punch 衝拳姿勢，以及 Big Bang 的原巨柱與回到站姿；另實際從 `native-growth.webm` seek 20、35、48、51、51.4、52、54秒取格，見原骷髏與巨球飛行、Big Bang由準備→原柱亮起→柱消失且本體重新施放骷髏。只聲明這些真正取樣，不把未取到影格的57／60秒當已看。

Firzen 最新手機自然局的母體取樣位於本體頭頂明顯較高位置，接續火／冰球才分裂並向敵群落下，符合原 opoint dvy−7 與20/30秒分裂順序；手機的炮／火山圖及影片20、40秒取格仍保有原像素輪廓、手部來源和可走路面。最終受控原生 `qa/{firzen,julian}/final-cycles/native-cycles.webm` 也各自真正seek 5、7、9秒並檢視；看見修正後母體上升、獨立火冰球與本體收勢，及 Julian 近身上勾拳和獨立巨球。再核對對應原生phase PNG含火山複合冰／火、球彈及柱的收束。這些Lv30受控片與Lv1自然成長分開標示。

`qa/firzen-final-cycles-source.json`、`qa/julian-final-cycles-source.json` 均為ok、errors空、sourceStable=true；獨立重新計算其全部 `sourceAfter` 路徑hash，與當前工作樹無差異。身份與動作來源複核無剩餘阻擋。Julian六項原招盤點與首發四教學＋基礎跑拳＋未移植Mirror Image的界線仍有效；不宣稱實體手機長局、完整原遊戲物理或真人聲音聽評。
