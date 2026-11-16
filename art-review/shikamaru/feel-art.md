# 鹿丸手感重做：動作與戰場讀法

使用者「都不好玩」已撤銷舊版作為完整候選的結論。舊92只檢查當時圖格/方向/入口，不能支持這次玩法完成；本文件是待實物驗證合約，不是放行。

## 玩家要讀到的因果

跑過的地方留下真正固定札；影子張開抓住一群；玩家再移動，普通敵才跟著影線被帶進札路；停步收網使同一群聚攏，起爆札按真延時逐張爆；首縛對剩下的被捕者形成可辨高潮。畫面必須讓玩家看懂「是我走過這裡，才在這裡收網」，不是又一批自動追蹤怪物的黑線。

## 現有30格的動作合約

| 真機制階段 | 身體與方向 | 可見後果/收勢 |
| --- | --- | --- |
| 行走佈札 | 原生walk雙腳交替；短投札使用前/背/側throwPrepare→ThrowRelease→ThrowRecover，方向取當輪投向 | 紙札從手端起飛後落到固定世界位置；身體不長時間借給札場 |
| 影捕捉張開 | Prepare→Seal；腳底為影源，方向取施放aim | 影面邊界向外膨脹，未接觸不演拘束；真接觸後敵腳底出現窄束環 |
| 模仿拖帶/走位 | 若玩家移動，回到真walk，不能持續crouch或Seal滑行 | 腳底細源線連至被帶者，敵人端點位置連續；已落地札留在原地，不能跟本體漂 |
| 停步/timeout收網 | 靜止者短Seal→Crouch，站立者可短Seal；不強迫停玩家輸入 | 影面輪廓收向真聚攏點，敵人移動由模擬決定，繪製不自行拖敵；真到位才扣傷害 |
| 札連爆 | 場域獨立，身體可走/出下一招 | 紙札引信逐張亮→自身位置爆→殘紙消散；先前札不瞬移到敵人腳下 |
| 首縛高潮 | Seal→Crouch/收緊→Idle；移動時用walk不把人鎖在原地 | 細影繞被捕者本體上升；頸部位置使用真bodyH，末段收束後回地，不畫到頭頂外 |

這些是現有圖格的語意分工。不能為湊段落拉長同一結印格、全身bob充當走路，或把Crouch拉成站高。當移動與短出手重疊，需要combat明列身體借用窗口；正常移動仍由輸入掌控。

## 保留真幅度，但去掉黑地毯

- 真碰撞外邊界保持完整幾何，建議內填深紫黑alpha .20–.34、外沿2px深邊，源端至已捕者保留約3–5px實線。透明度只改材質，不縮實際範圍或少算敵人。
- 影捕捉以真生長前沿畫輪廓；已釋放後不要每幀用新本體原點重畫此前範圍。若該招契約本來跟身，則所有顯示與碰撞同步跟身。
- 端點捕捉束環只在真held時畫，普通怪跟隨位移時束環/線端貼腳；強敵抗拖仍可固定端點，不能畫成已被拉動。
- 收網用真網邊/端點向真聚攏中心收縮，使玩家看見怪被聚到先前札路。不是把大黑面透明度漸淡後用粒子宣稱收網。
- 爆破依真多段接觸分輪，亮色集中當次札與命中圈；輪與輪間保留路面。手機低畫質減內紋和碎屑，不改輪數/真範圍/固定札位置。
- 首縛沿身暗帶與五指輪廓是主形，不用大圓罩滿整隻敵；黑影區仍需辨認敵彈/危險圈與可撤退方向。

## API待合約落地後才接

combat提供activeFor(actor)的真phase、phaseAge、phaseDuration、aim及moving；或明確action=throw/seal/crouch/walk/idle。Art facade只取樣，不創建技能clock，不改actor位置，不從performance.now猜階段。不以整招總age套0.65秒模板；每個新phase用局部時間。移動拖帶時應優先原生walk方向，短實際投擲/結印才使用攻擊aim。

本lane擁有shikamaru-art.js；combat擁有VFX draw。待gameplay/combat確認phase字段後只改必要映射，不動素材或共用Animator。

## 當輪驗收/退回條件

正常Lv1與幾張真卡都須看見：玩家走過的固定札路、影捕群、移動帶普通敵入陣、停步/timeout的明確收網、逐札連爆、末段回地。另看玩家撤退/跑動不中斷、強敵抗拖語意、牆前截止、手機與高數量地面可讀性。

若移除走位，怪仍自動被拉到同一批追蹤爆炸，視為新循環未成立；若移動全段結印滑行、札跟腳漂、黑影仍長時間蓋住路面、連爆只是一張大閃光，同樣退回。至少提供捕捉前/真接觸/拖帶中/收網/連爆首中末/收勢當輪原生相位，以及完整原生片。每次視覺修改前先記具體verdict；通過只能證演出與因果可讀，樂趣仍須用玩家實玩回饋判斷。

## 已落地的身體映射（本輪）

combat已確認phase=prepare/release/drag/net/blast/finish/recover，提供phaseAge/phaseDuration/moving。facade已接：prepare/release用當輪結印（trap獨立投札三相）；net按局部進度由Seal至Crouch，finish由Seal至Crouch再Idle。drag/net/blast/finish/recover若moving一律真walk雙腳且使用移動方向，不用攻擊aim扭轉撤退朝向。hurt/faint仍先於phase。

`node tools/test_shikamaru_art_phases.cjs`已通過：長總age不跳過新phase起手、net局部收網進度、移動各phase不滑行、移動背向不被aim覆寫、trap背向收勢與hurt優先。`node --check art-review/shikamaru-art.js`通過。這是程式回歸；新正常入口/影片/黑影材質仍待實看，不以此放行。

札出手補充：runtime短throwPose在札已釋出同幀建立，因此不倒播不存在的Prepare。phase=release局部前70%取ThrowRelease、末30%取ThrowRecover，保持真事件先釋放後收勢，沒有改札的時計。moving仍優先walk，不為高密度佈札永久吞掉腿部動作。

## 新版共享循環：本輪獨立實看

已重新從正常入口開局桌機/360/390，各Lv1、ready=true、pageerror=[]；證據在 `feel-qa/art-entry`（新尖影前）及 `feel-qa/art-pool-entry`（最新圓池尖影）。腳底/全身、選角五圖示與地面可辨。正常Lv1只用真鍵盤四向走位另留 `feel-qa/art-input`，沒有加等級/XP/改敵潮或推clock；其中drag/net/blast/finish移動時真walk。讀only log顯示drag moving=false但walking=true的49格實際位移全為0，是被障礙擋住，未將此誤判成滑行。

獨立實看 `qa/feel/native` 共享21相位中的捕捉、拖帶中、停步收網、持續移動timeout收網、連爆、首縛與收勢8個關鍵原生畫面。這是8張真卡配置受控百萬HP靶，並非自然局。`feel-qa/art-video/playback.json`及shared採樣證明Chrome真播放新shared-cycle、currentTime持續前進至片尾；沒有用舊片代替。

最終自然局來源為 `qa/feel/natural`（82.20遊戲秒、Lv7）；incomplete1/2不作完整依據。已用Chrome解碼其45.36秒原生片、成功seek並核對requested=actual，實看從Lv2至Lv7共8張採樣及首縛局部6張，檔在 `feel-qa/art-video/natural-final-*`、`natural-strangle-*`。特別核對影片41.4/41.6秒（HUD78/79）：真首縛30傷後再30傷，影線貼敵人而主角真向上跑；41.8秒顯示整備，42秒下一輪捕捉，首縛/收束/再捕捉成立。report只讀hurt ledger另有4次首縛、42札真爆，不以單純phase=finish冒充命中。

可辨的玩家因果：走過的札留在世界路徑；影線接住追兵，移動時腳與敵群端點連續；停步/timeout收網皆可進連爆，爆破和首縛不需鎖住本體；成熟群靶交會可短遮敵人，但主角/可撤退地面持續可辨。沒有聲稱真人已認可好玩，也沒有聲稱手機實機長局或音效聽評。

## 使用者追加影池/尖影要求：取代膠囊可接受結論

舊版膠囊影帶不再作最新放行依據。最新來源池以本體x/y真腳底為中心，常態半徑34，按當輪真延伸量及仍held連接縮小；不是可消耗技能資源或新硬限制。新枝寬根收尖，以真sim牆端點為尖端。最新正常入口桌機/360/390已親看，圓池中心貼腳底，尖影輪廓成立且沒有全身/手機裁切。

共享完整自然局與21相位屬先前影形；最新形狀另做短三四相定點補驗，明示來源差異，不冒稱影片已包含最後尖影版本。最後Contains根後隱傷數學修正不改畫面，幾何反例由QA處理；本lane不以自評掩蓋它。

## 最新圓池/尖影四相：獨立放行

已親看 `qa/shadow-shape/native/{initial,extended,held-after-rays,recovered}.png`。源池圓心貼實際腳底，初始圓半徑34；四枝伸長1200總長時縮至17.56，寬根連池、細尖端伸向真接觸；ray退去後仍held一條300長連接時池30.73，沒有錯在仍拘束時全恢復；最後held解除、整備時恢復34。該輪最小池半徑11.90，`report.json` sourceStable=true、errors=[]，combat來源bd7c6b3fd6f6ffd14bbea531b906ce644152756704e6e69f699f3d32f5def3e9。這是正常入口原生RAF加一個100HP靜敵的定點受控證據，非又一段自然局。

初始/最長/仍held/釋放四相的具體追加要求成立。新版完整循環、自然成長與最新形狀三組來源分開保留，未冒稱最後自然片含最新影形。當輪美術無未解阻擋，不新增素材、機制或擴拍舊相位；候選可交主代理做發布核對。新版verdict獨立存 `feel-qa/art-verdict-final.json` 與 `.omx/state/shikamaru-feel-art/ralph-progress.json`，91僅作這次具體視覺契約訊號，舊92不再使用。
