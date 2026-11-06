# 石流龍：花崗岩砲・圓環

新增獨立 Lv5 學習技能 `jjk-ryu-ring`。額前砲道先彎曲、逐步成環，再以持續的繞身砲束迎擊近敵；不是角色轉身掃射。原作來源與限制見 [動漫證據](research/anime-evidence.md)，實作後的獨立複核見 [轉譯審查](research/game-translation-review.md)。

## 本作行為

- 蓄力 0.32 秒，冷卻 6.5 秒。短身體動作結束後，圓環獨立持續，可移動並接原有砲擊。
- 一階基礎 4 輪，第一張數量卡 4→5；五階基礎 8 輪，數量上限 16 輪。每輪同敵只直擊一次；命中蓄能每次施放最多一格。
- 環半徑 112→180，砲道半寬 18→30。判定使用真正彎曲路徑的膠囊線段，牆及障礙依砲道順序截斷。初始接入砲道也能命中，成環後移除接入段，中央保留空洞。
- 跟身的有效幾何與可見砲道共用資料。低畫質保留完整寬度和輪次，渲染不製造傷害。沒有新增依賴、圖集或另一套傷害系統。
- 官方 PV 的斜俯視多層砲弧，轉為本作俯視平面圓環；數值、輪次、跟身及卡牌連動是遊戲改編。

## 變更範圍

| 檔案 | 用途 |
| --- | --- |
| `.omx/jjk-ryu.js` | 圓環狀態、曲線命中、輪次、清理與原技能並行 |
| `.omx/jujutsu-vfx.js` | 同路徑粗砲道與沿環流動的亮端 |
| `.omx/jujutsu.js` | 技能、圖示、共用成長資料及升階 |
| `.omx/jujutsu-growth.js` | 真實數量收益預覽 |
| `.omx/naruto.js` | 選角學習列與角色說明 |
| `.omx/naruto-skills-en.js` | 英文說明及升階 |
| `.omx/run-insights.js` | 蓄力／輪次 HUD |
| `tools/test_ryu_ring.py` | 戰鬥與成長合約驗證 |
| `tools/verify_ryu_ring_presentation.py` | 正常入口畫面、輸入、原生影片驗證 |

## 當次驗證

- `python tools/test_ryu_ring.py`：桌機／手機390通過，包含分散目標、4／5／8／16輪、中空、移動、外緣觸發、牆、主／次傷害回呼取消、死亡／換世界／局次、分身、合法學習／升階／數量卡與上限、唯讀繪製。
- 打包版本相同測試通過；證據 `.omx/state/ryu-ring/packaged/report.json`。
- `python tools/verify_ryu_ring_presentation.py`：桌機1280／手機360及390通過；45張相位畫面、三支原生 RAF 影片、實際鍵盤／觸控移動、選角五招列可見性與來源雜湊，見 [畫面報告](qa/presentation/report.json)。
- 既有巨砲回歸、JJK 程序特效回歸、42項成長合約、CombatPulse、catalog／boundary、JavaScript 語法及 `git diff --check` 通過；`python tools/build_digimon_site.py` 成功。
- 額外嘗試的舊 `test_ryu_identity.py` 仍斷言散射基數3，但修改前 HEAD 的技能資料已是4，故在該過期斷言失敗；本次保留既有散射行為，未把它改回3。這不列為已通過的回歸。

驗證為受控遭遇與階段等級下的真選卡；不冒稱自然XP完整養成、手機實機長局、音效聽評或玩家主觀樂趣。圓環在有效期結束時直接消失，沒有額外淡出傷害。本地實作及打包完成後，已依後續授權提交並發布；公開版本與核對證據見 [發布記錄](publishing.md)。
