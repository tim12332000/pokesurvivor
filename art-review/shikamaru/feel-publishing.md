# 鹿丸重做與圓池尖影發布

來源 `fc911b224d66e2ffb264d401c0657f37939e4d84`；正式靜態提交 `a9f3fdf558ac3445190517d45c561e56df8ec452`。Pages沿用原網址／HTTPS／legacy，source為 `codex/shikamaru-pages-fc911b22`，未改服務保護。

[直接遊玩新版鹿丸](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=shikamaru&release=fc911b22)。已完成公開核對並實際開局。

## 公開核對完成

15個公開檔案逐位元組同時符合靜態提交及canonical artifact，包括根入口、真正遊戲HTML、新影術／共享HUD／成長程式、metadata與圖集。詳細逐檔SHA位於 `.omx/state/shikamaru/public-assets.json`。

真Chrome由公開根網址在桌機、390及360手機視窗正常選鹿丸並從Lv1開局，三組素材ready=true且零pageerror；主代理另實看公開桌機畫面，腳底圓池及寬根尖影確實載入。結果與截圖位於 `.omx/state/shikamaru/public-browser-feel/`。這是公開可玩核對，不只是commit／push／queued。

## 這次改了什麼

- 四個獨立自動冷卻改為捕群、模仿玩家實際位移、沿真路徑留固定札、可提前／自動收網、連爆與首縛的一套循環。玩家可持續撤退，不被強拉或鎖住。
- 腳底有圓形影池，按真延伸與仍維持的影連線縮小，斷線後恢復。影枝寬根收尖，實際命中同用三角形與目標圓相交；已移除根後隱形半圓傷害。
- 第一張數量卡即增加真分枝、札容量與每札爆輪；預覽共用能力資料，技能欄改顯共享狀態。移除舊四組CD誤導，不新增依賴，未改弱其他角色。

主要檔案：`.omx/naruto-shikamaru.js`、`.omx/naruto-skills.js`、`.omx/jujutsu-growth.js`、`.omx/run-insights.js`、`.omx/naruto.js`、`art-review/shikamaru-art.js`及入口。

## 驗證與界線

[總監](feel-review.md)、[美術](feel-art.md)、[動漫](feel-anime.md)、[QA](feel-qa.md)各自記錄新的退回／補正，沒有沿用使用者否定的舊通過。來源摘要在 [feel-evidence.json](feel-evidence.json) 與 [尖影定點摘要](qa/shadow-shape/summary.json)。

十組新行為、五組有效舊安全回歸、九個標準Node檢查、phase回歸及相關語法／編譯通過。Q0／1／3首捕4／6／10；三札的追加爆輪用真hurt驗出3／6／12次。根中尖、牆、影池縮／held續耗／恢復另有當輪真命中及原生四相，來源穩定。

正常Lv1真選卡自然局到Lv7、82.20秒、HP235存活，五張已套卡、第六張升級卡仍待選；影首縛四次真傷、札七次真傷及42次真爆，停步與持續撤退皆完整收勢。該自然片先於最後尖形真幾何，後者另有當輪短片及Q捕群重驗，不混稱純繪製差異或同一來源。

未驗手機實機長局與音效聽評；主觀是否好玩仍待玩家實玩。既有無關角色報告改動保留未提交。
