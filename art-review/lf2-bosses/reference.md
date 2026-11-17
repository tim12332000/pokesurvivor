# Firzen／Julian：經典 LF2 2.0a 來源與動作合約

本輪使用經典 **Little Fighter 2 v2.0a**，不使用 Remastered、R-LF2 或 LF2.5 的改招素材。原圖、原音效與資料由 Marti Wong、Starsky Wong 製作；本專案程式授權不涵蓋原素材。人物直接加入選角與本作自動戰鬥，並非移植原版所有操作或引擎。

**現行範圍是 Firzen 原三招、Julian 原六招全部接入。** 使用者已否定先前省略 Mirror Image 的取捨；舊四招候選的完成通過已撤回。下方保留的舊影片核對只作歷史，新全六招候選已按文末重新驗收通過；歷史四招結果仍不作這次完成依據。

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

使用者已明確更正「全部技能」，先前將 Mirror Image 省略、Soul Punch 僅列為基礎動作的候選不再作完成依據。現行目標為 **原 readme 全六招皆正式進入學習與成長**：Skull Blast Lv1、Soul Punch Lv2、Uppercut Lv3、Mirror Image Lv4、Soul Bomb Lv5、Big Bang Lv8。Mirror 必須有原迴避移動、獨立非攻擊假影與真正影響敵人／追蹤彈的誘導，不能以攻擊分身或純裝飾殘影替代。完整候選重新驗收中；舊四招影片只保留為歷史證據。

## 目前證據界線

已核對：原包 SHA、原 readme 六／三招清單、所有列出的原 dat鏈、依賴物件／實體圖格範圍、原始細胞像素與 runtime SHA，以及 OpenLF2 特殊分派交叉佐證。

已獨立看過 `qa/firzen-desktop-normal-entry.png`、`qa/julian-desktop-normal-entry.png` 及 Julian 選角：Firzen 原綠髮、黃衣、披風與雙手冰火蓄能姿勢成立；Julian 原深色盔甲、面具紅眼、披風與掌中能量成立，身型比 Firzen 高大，腳底與地面陰影相接。該舊圖僅有四個 Julian 學習圖示，不符合使用者其後要求的全六招，不作完整候選完成證據。

仍待候選完整 phase：來源考據者須獨立看桌機／手機原生出招片段，涵蓋首段／後段／收勢及真正消散，再填本節。此時未把起始截圖稱為全部技能、玩法或完整畫面已完成，也未宣稱聽過全部原 WAV。


### Firzen 當次自然局取樣

已獨立看 `qa/firzen/natural-desktop` 的炮釋放／收勢、上升母體、分裂追擊、火山冰柱／地火／中央火爆與收勢圖。能辨識原雙手合炮、金色連炮、分離的原火／冰追擊球、原冰柱三段與原火爆圖；火山高峰短暫遮住本體，收勢即重新看見原角色和周圍路面。另用真正 ffmpeg seek 取出並實看 `native-growth.webm` 的20、35、45秒格：移動、本體收勢後在途冰火球與炮仍運作，角色與怪群有正常相對位移。這些是實際原生影片取樣，不聲稱完整逐格播放或聽評。

此桌機自然片製作期間另修正母體 lift 的升空先後；該片證明自然選卡與各招整體身份，最終升空→分裂關係仍以後續來源穩定的手機／受控原生片定點補驗，不冒稱早期片與最終產品每個byte相同。Julian 各招與 Firzen 最終 lift 版本取樣仍待補齊。


### 先前四招候選的歷史複核：通過已撤回

已獨立實看 Julian 自然桌機的骷髏逐發、上勾拳接觸與收勢、實體能量球、源300 Soul Punch 衝拳姿勢，以及 Big Bang 的原巨柱與回到站姿；另實際從 `native-growth.webm` seek 20、35、48、51、51.4、52、54秒取格，見原骷髏與巨球飛行、Big Bang由準備→原柱亮起→柱消失且本體重新施放骷髏。只聲明這些真正取樣，不把未取到影格的57／60秒當已看。

Firzen 最新手機自然局的母體取樣位於本體頭頂明顯較高位置，接續火／冰球才分裂並向敵群落下，符合原 opoint dvy−7 與20/30秒分裂順序；手機的炮／火山圖及影片20、40秒取格仍保有原像素輪廓、手部來源和可走路面。最終受控原生 `qa/{firzen,julian}/final-cycles/native-cycles.webm` 也各自真正seek 5、7、9秒並檢視；看見修正後母體上升、獨立火冰球與本體收勢，及 Julian 近身上勾拳和獨立巨球。再核對對應原生phase PNG含火山複合冰／火、球彈及柱的收束。這些Lv30受控片與Lv1自然成長分開標示。

`qa/firzen-final-cycles-source.json`、`qa/julian-final-cycles-source.json` 均為ok、errors空、sourceStable=true；獨立重新計算其全部 `sourceAfter` 路徑hash，與當前工作樹無差異。此僅證明舊四招候選的已看片段，不能證明全六招完成；使用者拒絕省略 Mirror Image 後，完整考據／動作驗收已重新開啟。未宣稱實體手機長局、完整原遊戲物理或真人聲音聽評。


## 全六招修正後的當前狀態

原三招 Firzen 的素材與像素證據保留；Julian 全六招候選須重新驗證原 Soul Punch 真前衝與 Mirror 的離身、假影、真敵方選目標／追蹤影響。先前final-cycles來源穩定只代表舊四招版本，不能覆蓋這次新行為。來源資料本身已包含全部106／103／104／105及240–251格，不需要補畫或借他人素材。


### Mirror Image 原資料精查（全技能修正）

| 原格 | 本體相對時間 | 原速度欄位 | 原圖與身體碰撞 |
| --- | --- | --- | --- |
|106|0–2/30秒|dvx0、dvy0、dvz3|pic78，存在bdy，原030聲音|
|103|2/30–13/30秒|dvx10、dvy0、dvz3|**pic49原像素全透明**，無bdy、無itr；不是缺失載入。此時從opoint產生假影。|
|104|13/30–17/30秒|dvx0、dvy0、dvz1|pic77重新出現，存在bdy，無itr|
|105|17/30–22/30秒|dvx0、dvy0、dvz1|pic78收勢，存在bdy；原hit_j可再接106|

103的opoint為oid52/action240、x39/y99，本體center34/99，因此原留影在釋出當格本體地面位置的面向前方5px，原Z另加1；不是追著本體跑的演員。假影240停26ticks，241–251共十一格各3ticks，總59/30秒；各格state15、dvx/dvy/dvz皆0，所有bdy與itr皆空。原pic78就是正常顏色的不透明Julian，後續來源格有自己的姿態變化；沒有資料指示改成攻擊分身、固定藍色幽靈或傷害球。

另實讀OpenLF2 `objects.lua` 的原opoint角色分派：新Julian假影hp/max_hp/dark_hp均10、mp5，繼承隊伍與owner/follow。`ai.prepare`把它列為活角色，選目標及追蹤球掃描依角色／隊伍／HP處理，不以bdy是否存在作瞄準資格。因此可吸引AI與追蹤彈，但**空bdy假影不是原版實體擋彈盾**：非追蹤彈照原航線飛行，追蹤彈可被誘向舊位置而失去真正本體。若本作另讓假影受擊消失或吸收彈體，必須標為改編，不能稱原始碰撞規則。

本體103沒有bdy的11ticks是真正避開身體命中的原窗口，106／104／105仍有bdy，不能把全部22ticks或假影全壽命寫成無敵。原資料同時要求真實位移與離開留影位置，僅播放透明圖而留原地並不完整。

OpenLF2 `control.lua` 的 `frame_velocity` 明確表明：dvx0不會清零現有vx，正數dvx只確保向面向方向的速度至少達指定值；`physics.lua`另逐tick扣1地面摩擦。故103的dvx10讓迴避主段持續前進，104／105的0讓慣性衰減；Soul Punch300／301的dvx15建立前衝，302以後0也不是立即停步。dvz3／1則依按住上／下與最近輸入設定。俯視本作可將此轉成依當下移動意圖的安全閃步／衝拳，保留撤退方向、牆碰撞與每步真實位置，不能以瞬移追敵取代，也不能把ITR的dvx25（受害者擊退）誤當本體速度。


## 全六招候選重新驗收：通過

本次重新核對的是 **Firzen原三招＋Julian原六招**。Julian當前正式學習項目完整含Skull Blast、Soul Punch、Uppercut、Mirror Image、Soul Bomb、Big Bang，並非舊四招加裝飾陰影。原普通拳仍是額外基礎動作，不代替正式Soul Punch。

已獨立檢視全六招桌機自然局的正式衝拳命中、Mirror準備／103消失／舊地假影／本體離開後重新出現／假影消散，以及六個完整HUD項目；手機390自然局相同Mirror相位可見原假影留在舊處、本體往不同方向移出再現，畫面與觸控區仍可辨。另真正ffmpeg seek新六招桌機自然片30、40、50秒，以及手機自然片47.5、50秒並實看，所見原骷髏飛行、巨球爆裂與分離本體／假影均與原圖一致，沒有攻擊假影或額外換色角色。

新 `qa/julian/final-cycles/native-cycles.webm` 以真鍵盤與原生RAF拍攝（受控Lv30／一階，各招及utility獨立展示），亦已真正seek5、5.8、6.1、6.9、9、12、15秒取格並逐一實看；重新看過其正式Soul Punch／Mirror103隱去、重現雙人、Big Bang完整光柱與回復原本姿勢等phase PNG。這些新的全六招證據與舊四招影片分開，不將未觀看部分稱作完整逐格或聲音聽評。

另讀過當前受控報告的真實防禦反例：原103時窗contact／projectile不傷，本體前後相位恢復受傷；native Enemy.update真的追向原位置假影，敵彈實際瞄準假影；同遭遇有Mirror損失0、無Mirror損失21，彈體穿過無bdy假影而不被吸收，幻影結束後恢復真人目標，地形／狀態傷害仍繼續。這些是模擬證據，不把單純計數器或回傳代理物件當作遊戲效果。

最終六招原生片來源 `julian-final-cycles-source.json` 為ok、errors空、sourceStable=true；獨立重算當前每個sourceAfter路徑，無產品內容差異。六招自然桌機／觸控片各自來源穩定，只有隨後註冊顯示檔的版本差異另保留，未冒稱與當前每個byte一致；最終原生片已對齊當前候選。Firzen的原三招與像素驗證結論保留，沒有因補Julian而刪減。

**考據與動作身份無剩餘阻擋，允許主代理依授權繼續發布及公開核對。** 原手動D/J/A輸入、完整原Z軸物理、實體手機長局、多人與真人聲音聽評仍是明示未驗／改編界線，不是缺少六個原招的理由。Soul Punch的30px受控前衝與依輸入的閃步，屬保留真位移／接觸及撤退意圖的自動戰鬥改編，沒有聲稱完全重現原摩擦慣性距離。
