# 螺旋手裏劍成長與長九尾窗口發布

2026-11-16。[遊玩新版鳴人](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=naruto&release=e26551ec)。

| 項目 | 版本 |
| --- | --- |
| 來源提交 | `e26551ecdb3cd77a69819195c65bd38b22764276` |
| 靜態發布提交 | `b975d9cecec7a1f64191768faaac40a525838d3a` |
| Pages 來源 | `codex/naruto-cloak-pages-e26551ec`，`/`，legacy |
| 前一發布來源 | `codex/scroll-pages-9cde2300`，其已提交卷軸內容保留於本次基底 |
| 公開版本清單 | [naruto-cloak-release.json](https://tim12332000.github.io/pokesurvivor/naruto-cloak-release.json) |

沿用原網址與HTTPS，CNAME仍為null，沒有改變服務保護。只提交本次鳴人技能、特效、對應測試與紀錄，工作區未完成的鹿丸修改及既有QA報告未混入發布。獨立canonical worktree從來源提交建置；靜態Git blob與canonical artifact、公開bytes三方一致。

## 公開驗證

- 15個關鍵檔案SHA256符合發布包，新增核對螺旋手裏劍實際戰鬥與特效程式。
- 公開根入口的桌機1100與直式手機390，首次及快取後重開均正常從鳴人Lv1進場，零頁面錯誤及本站素材失敗。
- 公開正常入口的受控技能配置核對所有五階：碰撞尺寸12/15/18/21/24、每階可見尺寸嚴格增加、普通藍色與九尾橘色配色、尾流與命中爆風、發射快照跨變身到期保持顏色。
- 真影分身與獨立卡牌分身正確承接其施放者的橘色狀態。
- 核心80%／外圈15%互斥；外圈延伸1.25倍半徑；範圍外與牆後不受傷；固體可破壞物不擋住自身命中；重複結算及取消回呼不補打後續目標。
- 九尾五階持續24/27/27/27/30秒，冷卻42/42/42/42/35.7秒，實際存活超過原12秒上限並按設定到期。桌機及手機另跑完整24秒原生窗口，確認到期還原。

以上公開檢查沒有攔截請求以本機資產替換；輸出位於 `.omx/state/naruto-rasenshuriken-release/`、`.omx/state/naruto-rasenshuriken-growth-public/`。完整窗口原始輸出位於 `.omx/state/naruto-cloak-release/public-window/`，本次發布紀錄另保存副本。測試程式與本機設計證據見 [驗證摘要](review.md)。

本次延用既有發布授權：標準九項Node、相關既有回歸、新成長／配色／擴散案例、正常進場與打包完成後才更新Pages；push與queued未當作成功。最後以公開檔案及瀏覽器驗證為準。

限制：戰鬥為受控技能配置、手機為瀏覽器模擬，未宣稱自然選卡長局、手機實機性能或音效聽評。
