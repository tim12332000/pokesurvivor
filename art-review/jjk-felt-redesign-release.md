# 讓玩家感受到技能：仙台角色重設計（2026-11-05）

本輪依使用者「好玩的點要讓玩家感受到」回饋，先更新企劃、美術、動漫 agent，再補做動畫能力盤點、角色重設計及羈絆精通崩潰修正。工程通過和真人覺得好玩分開；先前的視覺評分不代表使用者已認可設計。

## 已更新的 agent 與考據

- `design-council/gameplay/agent-instructions.md`：每招交代威脅、可見辨識、真實局面改變、下一步與少量成長；同遭遇移除此招仍看不出差異就重設計。
- `design-council/anime-art/art-agent-instructions.md`：核對敵方真反應與後續收益，不用光圈、彈字或評分冒充效果。
- `design-council/anime-art/anime-agent-instructions.md`：先完整盤點指定時期能力，分清遺漏、轉譯不足、改編、未確認與後期內容。
- `design-council/character-quality.md` 與專案／全域 skill reference 已同步，雜湊一致。
- [動畫技能盤點](design-council/anime-art/sendai-anime-skill-audit.md) 列出乙骨高出力放出、反轉與模倣等遺漏／候選，以及石流曲射、烏鷺近身偏折。官方已證實三方領域展開，名稱／內部效果仍不可捏造；舊 `jjk-anime-audit-v2.md` 已加更正入口。資料層級、未完整播放與待查項均有標記。

## 遊戲已改變的行為

**乙骨別動**：改成可與刀斬、完全顯現連拳並行的獨立反應。普通敵人停止移動、新攻擊、施法及接觸傷害2→2.8秒，強敵0.7→1秒；半徑240→320。已在途敵彈仍存在，DOT與原生狀態繼續老化。敵頭顯示停止與剩餘進度；恢復後射手有短讀招。這些時長、範圍與敵種規則是本作改編。

**乙骨高出力放出**：每次完全顯現中，既有刀拳真正收勢後，唯一里香移往可達側後陣位；乙骨與里香短蓄0.55秒，從戒指與實際嘴部各放出一道寬貫穿咒力。兩個來源有獨立傷害事件，沒有額外里香。射程600→840、每路半徑38→70；只有顯現也能使用此能力，但不免費得到協擊拳。沿用現有技能與卡槽，顯現到期、退學、死亡、清場、凍結均停止未結算內容。嘴點依現用Roar圖格實測，HUD有就位／蓄力／放出真階段。

**石流散射**：四路先分岔再真曲射，各路依角度分配不同敵人，沿每四單位線段做轉向與掃掠碰撞；沒有畫彎線卻算直線。第一張數量卡四→五路，上限九路；牆阻、首接觸、同施放去重及一次蓄能保留。近距60／100／140皆在一秒內命中，避免近敵被最外路搶走而全空。

**烏鷺天空幕**：除了敵彈，也會接走有實際來源的近身接觸。普通攻擊耗一容量並施加切向偏折，強敵耗兩份且不被搬動；容量耗盡仍會受傷，不新增通用無敵。近身／敵彈首次攔截共用一次反擊鏈，沒有重複或遞迴反擊。HUD改成「等來襲」。

**羈絆精通崩潰**：乙骨已學顯現、尚無戰鬥狀態時，HUD的 `s?.manifestUntil > s.clock` 仍解引用空值。連續畫面例外會觸發遊戲錯誤退出，符合使用者「顯示錯誤後跳回主畫面」。已加完整空值保護，以真選卡、原生畫面時鐘驗證修正；未用泛用重試掩蓋例外。

## 修改範圍與簡化

角色：`.omx/jjk-yuta.js`、`jjk-ryu.js`、`jjk-uro.js`。共享資料／HUD／繪製：`.omx/jujutsu.js`、`jujutsu-growth.js`、`run-insights.js`、`jujutsu-art.js`、`jujutsu-vfx.js`。原生停止與接觸接點：`js/entities/enemy.js`、`player.js`、`js/systems/combat.js`、`self-clone.js`。

移除舊咒言「先完整執行敵人行動、再回縮位置」的做法；沿用單一里香與現有圖格，能力 profile 同供戰鬥與卡牌預覽。未新增依賴、新角色圖集或第六技能槽。保留開工前與前輪既有變更。

## 驗證證據

- 別動：`.omx/state/yuta-speech/after/report.json`。桌機／390px手機真Enemy.update、原生Combat.resolve、DOT、密集分離、階數／範圍、取消與有無技能影片。單步無招移23.4／射擊1、有招移0／射擊0；完整含到期影片仍可看到恢復後攻擊。
- 放出：`.omx/state/yuta-release/after/report.json`、`final-check/report.json`、`duet-regression/report.json`。雙源各命中三個分散目標、範圍外、牆、24拳收勢、同一演員、每顯現一次、停止／到期／凍結回呼及物件中止。含桌機／手機完整原生片。
- 曲射：`.omx/state/sendai-redesign/ryu-close-fix/report.json`。同五敵對照普通砲命中一名、無卡散射四名、第一卡五名；近距60／100／140、牆、移除與取消檢查通過，附更新的四段原生片。
- 偏折：`.omx/state/uro-deflect/after/report.json`、`callback-after/report.json`、`fracture-regression/report.json`。本體與分身真傷害流程、來源／牆／距離、強敵、容量、兩種攔截順序、生命週期，以及施放回呼移除／擊殺／移動／隔牆均覆蓋。
- 羈絆：`.omx/state/bond-mastery-runtime/after/report.json`；打包後再驗 `.omx/state/sendai-felt/built-bond/report.json`。修正前重現空值堆疊與錯誤退出；修正後桌機／手機真按鈕、學顯現、尚未施法／清場後選卡，HUD無錯、時鐘暫停、成功只扣一次且恢復遊戲。
- 獨立視覺：`.omx/state/sendai-felt/independent-visual.json`、`ralph-progress.json`。曲射真軌跡、烏鷺有無技能的真威脅對照、別動普通／顯現併發、雙源錨點、本體可辨與末段收勢；評分只代表具體視覺目標。
- 既有系統：八項現行CI Node檢查、全部變更JS語法、Python編譯及diff檢查通過；共享分身傷害另做我愛羅場景／護盾回歸。舊測試啟動器不支援現行非同步／iframe入口，使用現行正常入口boot後執行原CHECK通過，見 `sendai-felt/clone-regression/report.json`。
- 打包：`tools/build_digimon_site.py`成功；`sendai-felt/built-entry/report.json` 三角色桌機／手機正常入口、真鍵盤／觸控、學招、美術、傷害與生命週期通過。舊咒言測試已改驗獨立反應事件與強敵提早恢復，沒有刪除有用案例；整合檢查實際抓到並修正曲射近距漏打。
- `sendai-felt/package-hashes.json` 核對12份實際runtime與打包位元組一致。

## 交付與實玩界線

本機試玩：`http://127.0.0.1:8368/.omx/digimon.html?lang=zh-TW&release=sendai-felt`。本輪產出在工作樹與 `dist-digimon`，沒有更新公開站。

反轉、更多模倣與領域的遺漏／證據已盤點，本輪沒有宣稱全部實作。放出視覺影片用零傷敵人隔離演出；真正威脅差異由別動／偏折的獨立有無對照支持。未驗實體手機熱降頻、完整自然養成長局、真人連線或主觀好玩；玩家實玩回饋仍是設計是否成立的必要依據。
