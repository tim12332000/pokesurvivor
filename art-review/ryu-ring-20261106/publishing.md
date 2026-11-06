# 圓環砲發布記錄

[遊玩石流龍](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=ryu&release=81d3b3da)。圓環在 Lv5 選卡學習。

| 項目 | 值 |
| --- | --- |
| 遊戲來源 | `81d3b3da1fdd40d0188a7572fac1a691c8ba4047` |
| canonical 靜態發布提交 | `adde01f2be02e9668aab013656d072398c7e570b` |
| 前次公開提交 | `10313fd9da0ac45ec3cecef6f4aeb8b5d670bd87` |
| Pages 來源 | `legacy`、`codex/ryu-ring-81d3b3da` 分支 `/` |
| GitHub 部署 | `7602782604`，2026-11-06 22:45:30（台北）回報 `success` |

使用獨立 `core.autocrlf=false` worktree 建置，七份變更執行檔的 bytes 均符合 Git blob。相較前版公開包只改動七份 JS 及入口版本碼，共八檔；共用既有動畫與碰撞資料，沒有新增依賴、圖集或額外傷害系統。網址與 HTTPS 保留。

九項標準 Node 檢查、JS 語法與 diff 檢查通過。canonical 打包版的圓環桌機／手機合約、既有巨砲回歸、JJK 共用程序特效回歸全部通過；初次本機巨砲回歸曾在開局載入逾時，打包版重跑正常。

公開入口及八個關鍵檔案的 SHA256 全數符合發布包。桌機1280、手機360及390正常 Lv1 開局後，以階段等級及原生選卡學會散射與圓環，驗到自動施放、四個分散目標各實際扣血428、動作與環結束清理；無頁面錯誤、HTTP載入錯誤或水平溢出。這是受控選卡／遭遇驗證，不冒稱自然 XP 養成或真手機長局。

公開核對證據見 [發布與檔案雜湊](qa/public-release.json)、[瀏覽器結果](qa/public-browser.json)。完整當次本機紀錄與畫面位於 `.omx/state/ryu-ring/`；原始影片與研究圖片未加入公開包。

尚未驗證手機實機長局、音效與自然 XP 全程養成。既有過期散射基數測試的限制保留於 [實作記錄](implementation.md)，本次沒有將現有散射改回舊數值。後續文件提交不改變上述已發布遊戲來源。
