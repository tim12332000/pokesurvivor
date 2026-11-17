# Firen：經典 LF2 2.0a 完整招式考據

本次採用舊版 Little Fighter 2 v2.0a 原圖、原動作及原音效，不用 Remastered 或改招版，不用生成圖取代角色。原作為 Marti Wong、Starsky Wong；遊戲免費不等於素材開源，本專案程式授權不延伸涵蓋原素材。

## 已實際讀取的來源

- 原版安裝器為既有 `art-review/freeze/source/LF2Setup.exe`，29,586,263 bytes，SHA256 `540c485547e234b0d09595f54d067aafd7176092c308aca61868f3cbc03030e1`。來源是 [Internet Archive 的固定原包](https://archive.org/download/little-fighter-2_202404/Little%20Fighter%202.rar/Little%20Fighter%202%2FLF2Setup.exe)。只作資料讀取，沒有執行安裝器。
- 原包 `readme.txt` 的 `==Firen==` 明列四招：Fire Ball、Blaze、Inferno、Explosion；輸入分別為 D→A、D→J、D↓J、D↑J。Explosion 標示 `60mp + 8hp`。原 readme 及 SHA 已保存。
- 原包 `data/data.txt` 對應角色7 `firen.dat`、物件210 `firen_ball.dat`、211 `firen_flame.dat`。直接解密並讀取這三份資料，保留 `pic/wait/next/centerx/centery/opoint/itr/bdy/mp`，不憑招式名稱猜出實際碰撞。
- `.dat` 外的成本／壽命／合體語意以 [OpenLF2 的同版本 primary source](https://github.com/OpenLF2/OpenLF2/tree/bf68b8ba975a93d90d10818837b48adda682faad/scripts/base/game) 交叉核對：`control.lua`、`constants.lua`、`animation.lua`、`item.lua`、`physics.lua`、`objects.lua`、`merge.lua`。這是獨立重實作，並非原版官方引擎原始碼。`merge.lua` 本輪從固定 commit 讀取，其餘既有研究副本已逐項實讀；不以搜尋摘要當作功能證明。

重建：放入相符原安裝包後執行 `python tools/build_lf2_firen_assets.py`。重用既有安全 reader／RLE8 decoder，只需工作區已有 Pillow，沒有新增依賴。輸出 `assets/lf2/firen/manifest.json` 及7張PNG、16份WAV；原安裝器、解密全文與研究原碼不加入正常開局包。

## 原圖與 metadata

保留原格內像素；只把 LF2 純黑色鍵與原遊戲忽略的1px彩色圖格分隔行／列轉為透明，避免非整數縮放滲出矩形邊。已逐像素核對 **1,762,755** 個格內像素完全一致，runtime 檔案 SHA 記在 manifest，摘要為 `pixel-verification.json`。

角色三張身體表皆79×79格／80px步距，原 center 錨點隨格保存，不用每格 alpha 外框放大。站姿原 alpha 外框為 `(20,12,58,79)`，腳底79；本作 nominal bodyHeight65 與既有 LF2 人物一致。`firen_ball` 為81×82，口部火焰59×63，地火35×49，大爆炸159×159；各圖格尺寸／分派由原資料取得。

## 四招完整來源合約

原模擬30fps，一格停留 `(wait+1)/30` 秒。以下 tick 以各招起始計算。

| 原招 | 原身體與接觸鏈 | 必須保留的能力關係 |
| --- | --- | --- |
| Fire Ball／D→A(+A...) | 235→240共13 ticks，238於6 ticks從手前 `(68,44)` 放 oid210 action0。追加241→246、247→252各13 ticks，244／250同樣在各自6 ticks出波，原手勢不同。 | 球真正飛行、接觸燃燒，身體收勢後在途球繼續。原球0–5各2 ticks循環；frame0 center為 `(51,41)`，ITR `x22..77/y27..54` 相對該 center 沿向中點−1.5、半長27.5、半寬13.5。各格的 center 必須從 metadata 取，不能套其他角色的球錨點。撞擊10–13是無 ITR 的8 ticks消散，不能把原撞擊圖冒稱免費範圍爆炸。自動有限連射與成長量為本作改編。 |
| Blaze／D→J | 255起手3 ticks，256於3 ticks開始 `dvx:10` 移動；257於6 ticks起有本體攻擊與腳後地火50。之後261→258→259→260→261，每3 ticks出接觸／地火，12 ticks成一循環。停止218共6 ticks。 | 角色本體真正移動、沿走過的位置留原地火，原火焰衝刺圖與身體接觸相符；不是原地火圈或瞬移。輸入反向與障礙要真的影響前進，不強迫撤退中的玩家回頭追怪。原255–261仍有 bdy，沒有原生全程無敵。 |
| Inferno／D↓J | 267→268→269→270→271，271於9 ticks從嘴部 `(42,41)` 放 oid211 action0；274於15 ticks再放。270–275的12 tick循環每6 ticks吐一團，283為4 ticks收勢。 | 連續嘴部火流，有明確的準備、各次釋放、火焰飛行及收勢。原 flame0的小火苗可見但無 ITR，2 ticks後進1才可傷害；1–9→100–104為真正活躍火團，整體30 ticks後消失。不能把無攻擊的0框判為已命中。 |
| Explosion／D↑J | 285→293共34 ticks，289於8 ticks發 oid211 action109 `(48,81)`。109為2 ticks透明前置，110–117有效於效果2–18 ticks，118–120再6 ticks消散；效果總24 ticks。 | 本體附近原巨型火爆炸、真實範圍與完整消散；起手及透明109不能提前傷害。285原MP欄4300含生命成本，身體286–290有 bdy，不能順便給沒有來源的無敵。 |

普通拳60／65各7 ticks，61／66於3 ticks起接觸；原重拳及跑擊格保留在 metadata，但不是把普通格硬湊成第五個 readme 特殊技能。四個 named abilities 都需要真實遊玩功能和正常選卡，而非僅放名字／圖示。

### 地火與 Inferno 的來源界線

地火明確來自 Blaze 身體257／261／258／259／260的 `opoint action50`。50→51的51於2 ticks再產生54子火；52於4 ticks出第一個 ITR，52–59每16 ticks循環，命中 vrest20。57的 `hit_a:60` 在原引擎每 tick 消耗火物件自身HP，耗盡轉70–73的8 ticks退場。原物件初HP500，故 nominal parent 大約2.87秒含退場，子火約2.6秒；本作若使用固定有限生命／命中節奏，須標成俯視生存改編，而不是假稱 `.dat` 有固定秒數。

Inferno 的 action0→104 沒有生成 action50 的 opoint；讀過的 primary objects／physics／combat 也沒有證明它結束時必然產生地火。原 ball kind 不受重力，火團由嘴部高度飛行後消失。因此不將「Inferno 必定落地留火」當成原作既有能力；Blaze 的地火則不可省略。口部火團、地火和爆炸是三套不同圖格／活動窗，不能混成同一個瞬間火圈。

### Explosion 生命成本

原 readme 的 `60mp +8hp` 使用100單位描述；原引擎常規HP／MP為500。`control.enter_frame` 以 `mp %1000` 為MP成本、`floor(mp/1000)*10`為HP成本，故285的4300實際是300MP＋40原引擎HP。成本在進285起手時扣除，嚴格要求現有HP大於成本。若本作採8%最大生命、在釋放時才扣、或不讓技能自殺，均需在能力資料與說明交代這個改編，不將它冒稱原引擎原數字／時點。

## Firen＋Freeze 合體：另行盤點的雙角色規則

原合體並非 readme 的第五個 Firen 特殊招式。primary `merge.lua` 對實際同隊 Firen7、Freeze8檢查：雙方活著、原HP都低於177（常規500的35.4%）、merge timer為0；發起者跑步，另一角色也跑步（生成NPC槽>9有落地非倒地例外），`|dx|<50`、`|dz|<8`，另有槽位／左右位置限制。成功後原生Firzen51、frame290，合併生命後封頂、移除另一角色；150秒合體時間後在允許的原動作狀態分離，並有30秒再合體恢復。

主代理明確決定本輪完成四個原 named skills；雙角色的合體／移除／分離及多人同步系統不在此單一角色新增中實作。這個原規則沒有被藏起來，也沒有用假 Freeze 夥伴或單人低血量自動變 Firzen 冒充。既有可選 Firzen 亦不等於已完成合體系統。

## 當次畫面驗收

已獨立實看本輪 `qa/firen-desktop-normal-entry.png` 與 `firen-desktop-selection.png`：原金髮／紅肩、紅腰與深色服裝、雙手出火姿勢及站姿皆與原格辨識一致，腳底與地面陰影穩定；四個正常學習圖示1／3／5／8均可見，選角縮圖亦已畫出。本段只確認當次入口身份，不替代四招完整接觸／後段／消散。

### 四招原生與自然流程：獨立複核通過

已獨立實看桌機自然局四招準備／釋放／收勢、火球與口部火焰獨立飛行、Blaze 地火和大爆炸成形／消散 PNG。原火球的手前亮球與尾焰、原燃燒跑姿及實際前進後留下的地火、由嘴部連續放出的原小火舌，以及原159格大爆炸是可區分的能力。本體只有爆炸高峰短暫被遮，原煙塵散去後能重見身體、敵人與路面，沒有持續滿屏白光或圖格矩形邊。

另以真正 ffmpeg seek 取出並實看桌機 `native-growth.webm` 的20、24、26、29、35、42、43、44、45、50秒格，看到正常相對移動、兩次火球、地火留下後本體離開、合法升級選卡，以及爆炸收束。43秒是實際選卡畫面，不冒稱當段仍在戰鬥。手機原生影片實看20／40／50秒格及其爆炸 active／fade／final 圖：原角色與火焰在390寬下可辨，觸控區與可走路面仍可辨，四個 HUD 均可見。這些瀏覽器觸控與短局證據不是實體手機長局或真人樂趣認可。

最終受控原生 `qa/firen/final-cycles/native-cycles.webm` 的當前影片長11.04秒，已真正seek並實看5、5.7、6.1、6.3、6.8、7.1、8、10秒格：手前火球、移動火身與獨立地火、嘴部火流、原巨火爆炸與後續清空均成立。2秒為載入白畫面；12／15秒超出長度，沒有把未取到的影格稱為已看。影片不是靜圖拼接；Lv30受控靶與Lv1真選卡自然局分開使用。

`qa/firen-final-cycles-source.json` 的結果 ok、errors空、sourceStable=true；獨立重新計算全部 sourceAfter 路徑 SHA 與當前候選相同，零差異，證明保存於 `source-review-provenance.json`。來源／動作身份複核沒有剩餘阻擋，見 `authenticity-verdict.json`。聲音出自原包及程式事件路由，但沒有宣稱已作真人音色／混音聽評。原版生命成本與本作8%最大生命、釋放時扣除的改編，及另行雙角色合體規則的界線仍明列。
