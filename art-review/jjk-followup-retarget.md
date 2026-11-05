# 三角色接力與追擊改善（2026-11-05）

本輪由四個原生子 agent 分別處理乙骨、烏鷺、石流與獨立美術／動漫審查，主代理整合共同說明、程序特效及打包驗證。沿用現行火影手感基準、技能資料與素材，不新增依賴或原作能力。

## 玩家能感受到的變化

- 石流：普通砲、散射、爆破每次施放首次真正命中各蓄一格，三格接巨砲。多彈／多目標同次仍只一格；空打、牆、物件、巨砲不蓄能。取消後也不補蓄，學會支援招能推進招牌高潮。
- 乙骨：同一里香失去原靶後，在射程與剩餘移動預算內轉打有效敵人，沿用剩餘拳數及獨立接觸索引；無目標就返回。修正24拳間隔下追身窗口為空的問題。已移除但仍留在空間索引的敵人不能再次成為目標或受擊。
- 烏鷺：宇守羅彈首波保留原瞄準，後續逐波追蹤有效原靶，失效後轉向可達敵潮。舊命中痕、固定震落及末波衍生殘響保持已結算幾何。移除敵人的舊空間索引不再參與索敵或扣血。
- 一般砲：特效細節預算耗盡時沿用真實半徑，以簡單填色輪廓保留粗束和亮芯；不再退成細線。沒有增加傷害事件或額外演員。

## 修改範圍

角色邏輯：`.omx/jjk-ryu.js`、`.omx/jjk-yuta.js`、`.omx/jjk-uro.js`。共同說明：`.omx/jujutsu.js`。簡化砲束繪製：`.omx/jujutsu-vfx.js`。

回歸：`tools/test_ryu_barrage.py`、`tools/test_yuta_duet.py`、`tools/test_uro_fracture.py`、`tools/test_jujutsu_vfx_runtime.py`。保留開工前已有的石流取消修補、`.omx/jujutsu-growth.js` 與 `tools/test_growth_contract.cjs` 成長預覽變更。

## 本次驗證

新增案例先重現舊版失敗，修正後通過：

- 石流桌機／390px手機完整專屬測試、原生自動三招蓄能接巨砲、HUD、取消與命中邊界：`.omx/state/three-hero-followup/ryu-after/report.json`。
- 乙骨桌機／手機完整協戰測試及原生影片：`.omx/state/yuta-retarget/after/report.json`。移除原靶後幽靈零命中、新靶接三拳且共鳴一次：`yuta-retarget/stale-grid/report.json`。
- 烏鷺桌機／手機完整裂面測試、原生影片、四演員短測：`.omx/state/uro-turning/after/report.json`。追加移除敵人舊索引案例及完整 CHECK：`uro-turning/stale-after/report.json`。
- 正常入口程序特效測試：`.omx/state/jujutsu-vfx/report.json`。同一真實普通砲以受控預算6／0畫至透明畫布，中央厚度修正前24／4像素，修正後24／24像素；繪製前後傷害不變。
- 獨立視覺審查：`.omx/state/sendai-continuation/independent-visual.json`。包含三角色桌機／手機相位圖、六段影片各首中末採樣；不是完整逐幀或音訊聽評。
- 普通砲正常390px畫面迭代：`.omx/state/sendai-continuation/ralph-progress.json`，最終92／pass。強制耗盡預算只證明簡化分支畫法，不代表自然多人發生頻率。
- 打包入口三角色桌機／手機、鍵盤／觸控、學招與美術接線：`.omx/state/sendai-continuation/built-entry/report.json`。
- 八項現行 CI Node 檢查、變更 JS 語法、Python 編譯與 diff 檢查通過；`tools/build_digimon_site.py` 成功，打包 runtime 與來源雜湊核對。

## 交付與限制

本輪為本機工作樹與 `dist-digimon` 打包成果。試玩服務 `http://127.0.0.1:8368/.omx/digimon.html?lang=zh-TW`，可用正常選角進入三角色。

實體手機熱降頻、完整自然養成長局、真人連線與主觀樂趣仍待實玩。受控高配與影片不能代替這些結論。既有火影角色未修改；本輪沒有推送或更新公開站。
