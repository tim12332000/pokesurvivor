# 宇智波斑可玩版本

> 此頁是已被使用者否定品質的初版紀錄，保留作歷史，不再構成完成依據。現行重製與新證據見 [重製交付](release-v2.md)。

入口：<https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&hero=madara>

## 玩家可見改動

新增忍界大戰穢土轉生宇智波斑，ID 30016。專屬16格動作圖集，黑長髮、紅色板甲，正常選角列與開局皆接入。

| 學習等級 | 招式 | 行為 |
| --- | --- | --- |
| 1 | 戰場演舞 | 四段短距掌擊衝擊，第一張數量卡變五段 |
| 3 | 豪火滅卻 | 口前寬幅多波火幕；前三張數量卡為4→5→6→7波 |
| 6 | 須佐能乎 | 具身巨刃連斬與更強末刀，數量卡最多16斬 |
| 9 | 天礙震星 | 兩顆獨立預告、落地與命中的固定落點巨岩，後接多輪衝擊 |
| 12 | 木分身 | 有連續位置與自身出手源點的實體協戰，依已學技能使用須佐／火遁／體術 |

五招自動施放、不占主動槽。木分身各階火力倍率100%→120%→145%→175%→210%，不把人數不變的階數當成無效升階。全部數量消費者有上限，上限後不提供無效數量卡。無敵人時仍可攻擊可破壞物。

## 主要變更檔案與共用方式

- `.omx/naruto-madara.js`：專屬資料、學招、真多段戰鬥、木分身與HUD；施放和卡牌共用profile/vector。
- `.omx/naruto.js`、`.omx/redrawn-init.js`、`.omx/naruto-en.js`：角色尾加、選角、載入、中英文接線。
- `.omx/combat-pulse.js`：可選cast目標合法性檢查，逐筆直擊／擴散排除已移除目標；其他角色保持原契約。
- `art-review/madara/runtime.js`、`frames.json`、`madara-actions-v1.png`：只讀取樣與繪製，不用繪製時鐘造成傷害。
- `tools/build_madara_assets.py`：從原始透明圖集建立圖格與腳底錨點。
- `.omx/make_digimon.py`、`tools/build_digimon_site.py`、`.omx/.gitignore`：正常入口、打包與素材SHA256一致性。
- `tools/test_madara.py`、`tools/test_combat_pulse.cjs`：專屬接受測試與共用邊界回歸。

沿用既有數量卡、升階、World物件傷害與CombatPulse歸屬管線；沒有新增依賴或另一套成長系統。既有角色不為新角調弱。

## 迭代與證據

動漫、美術、戰鬥、測試與獨立讀碼審查交叉修正。解決首張數量收益、多段姿勢時鐘、口前火源、須佐輪廓、暫停隕石消失、木分身假傷害成長、可破壞物接線及空間索引殘留敵人。

設計／美術與審查記錄：`anime-design.md`、`anime-review.md`、`art-provenance.md`、`art-review.md`、`code-review.md`。凍結版接受測試資料、相位圖及原生影片在本機`verification-final/`，早期迭代保留於`verification/`，美術各輪相位在`art-verification/`；展示片不加入正常遊戲下載。

最終機械驗收與來源一致性以`verification-release/report.json`為準：桌機／390／360正常入口、真鍵盤／觸控、全部機械及即時升階卡預覽通過，errors／missing／failures均為空，測試前後來源雜湊一致。`verification-low/report.json`另驗360低畫質，同樣通過。

`verification-final/report.json`的完整相位與各18秒原生RAF錄影均通過；這份證據早於最後一次即時升階卡文案修正。最後修改只影響選卡預覽，戰鬥與繪製不變，定點重驗後保留原片而不重拍。

現有8項CI基線、6個相關JavaScript語法檢查、Python編譯與diff空白檢查通過；實際發布包可選斑並正常開局，無頁面錯誤或漏載，關鍵腳本／圖集與來源一致。發布結果另由本次提交的GitHub Pages workflow與公開資產核對確認。

## 實際限制

上下使用側面、向左鏡射，沒有獨立八方向。火焰、須佐與巨岩使用簡化程序材質。360／390手機viewport、受控高配與原生短片均不代表實機長局效能、完整自然成長或玩家已認可樂趣；聲音沒有獨立聽評。
