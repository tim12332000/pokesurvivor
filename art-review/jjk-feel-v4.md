# 仙台角色 v4：移動接觸、協同追擊與爆發節奏

版本：`sendai-20261105-feel-v4`。使用者先要求優化現有企劃、美術、動漫 agent，再改善新角色並直接發布。本輪未改動既有火影角色的戰鬥與美術模組。

公開試玩：[乙骨](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=jjk-yuta&release=feel-v4)、[石流](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=jjk-ryu&release=feel-v4)、[烏鷺](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=jjk-uro&release=feel-v4)。公開版沿用正常一級成長。

## Agent 先更新

三位獨立 agent 從現行小李、八門、我愛羅、手鞠等實作提煉可轉移原則，分別更新企劃、美術、動漫指引，再交叉檢查。以 `AGENTS.md` 和 [現有角色入口](design-council/charter.md) 接上後續任務，不修改通用模型設定。舊的 design-council 設計會議紀錄保留，另標明歷史範圍。

改進重點是：實際普攻空檔、接觸與追擊、可見成長、獨立演員及招式高潮；動漫由造型／招名考據延伸到動作鏈與相對位置，美術對齊現用圖格與真實命中。不能照抄歷史提案、用加傷害取代設計，或把測試通過稱為玩家主觀覺得好玩。詳見[互評](design-council/agent-update-review.md)。

## 角色改動

| 角色 | 實際差異 | 保留的短板 |
| --- | --- | --- |
| 乙骨 | 刀斬／咒言跟本體到命中；里香接近原本強敵時有限追擊，起拳後固定落點。 | 方向起手鎖定、普通敵人固定落點、里香不能穿牆或無限追擊，起拳後能被躲開。 |
| 石流 | 全力砲基礎冷卻 11→5.4 秒，接上三次真命中的蓄能回報；短箭頭顯示已鎖方向，走位仍能調整砲線。 | 三次命中、取代下一發普攻、0.75 秒鎖向蓄力與0.7秒恢復保留，移動目標仍能閃開。 |
| 烏鷺 | 身前掌擊／碎面跟本體至釋放，命中後固定；三階反射接力優先反擊有效原射手。 | 遠端震落固定；未知／網路彈沒有可信來源時沿用原索敵，反射仍限次且不抗近戰。 |

烏鷺程序折面的目的區域隨出招移動，來源背景保留一次捕捉；接觸後不再跟人拖動。不新增圖集、依賴或通用震屏，未提高單擊基傷。追擊與索敵是本作遊戲改編。

逐角證據：[乙骨](jjk-feel-yuta.md)、[石流](jjk-feel-ryu.md)、[烏鷺](jjk-feel-uro.md)。

## 修改接點

- 後續 agent 路由：`AGENTS.md`、`art-review/design-council/charter.md`、`README.md`、`agent-update-review.md`；企劃與動漫／美術目錄內的職責指引與現行基準。
- 戰鬥：`.omx/jjk-yuta.js`、`.omx/jjk-ryu.js`、`.omx/jjk-uro.js`；`js/entities/enemy.js` 只新增原生敵彈的發射者參照。
- 呈現與說明：`.omx/jujutsu-vfx.js`、`.omx/jujutsu.js`；`.omx/digimon.html` 更新實際腳本雜湊，`version.json` 標記版本。
- 驗證：`tools/test_yuta_feel.py`、`tools/test_uro_feel.py`、`tools/profile_ryu_feel.py`、`tools/test_jujutsu_vfx_runtime.py`。

## 當次驗證與限制

修改前後桌機／手機的受控幾何確認：舊原點不再傷害，新原點三個有效目標受擊，範圍外不受傷；里香移動強敵、碰撞、鎖點與預算；反擊來源失效回退與一次消耗；暫停、死亡與清場。既有三角色 identity 回歸、卡牌／pulse／獎勵契約、CI 八項 Node 檢查通過。

三角色桌機／手機六組原生 RAF 遊玩通過，含真實鍵盤／觸控移動與已學招式自動出手。324 組比較涵蓋三角色、10／19／35張等成本選卡、三配裝、四遭遇、三種子，未發現受測矩陣中的結構收斂或全面支配。石流另有12組60秒前後配對，蓄滿後等待自身冷卻由約18–21秒降至0；沒有宣稱移動首領命中率普遍提高。

VFX 高／低品質、DPR1／2、移動原點、來源捕捉／目的矩形分離、鎖向提示、關閉不改傷害，以及接觸後固定回歸通過。美術 agent 以實際準備／接觸／收勢畫面與位置日誌複核，修正過收勢取樣仍處接觸階段的測試證據。

本機原始證據：`.omx/state/feel-v4/`、`.omx/state/jjk-feel/ryu-baseline/`、`ryu-final/`、`.omx/state/jujutsu-vfx/`。這些受控比較不等於真人主觀手感、完整長局平衡或實體手機熱降頻驗證；本輪目標是讓玩家拿到可玩改版繼續回饋。
