# 俯視圓環砲發布記錄

已上線：[遊玩石流龍](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=ryu&release=48a22f71)。

| 項目 | 實際值 |
| --- | --- |
| 遊戲來源 | `48a22f7185237ac12bd049335fc0deec7243363e` |
| 最終靜態發布提交 | `1c38f032605901d9a80d94e7b179377e414671a2` |
| 初次卡住的靜態提交 | `3d12956e5127fc27e6a2004db36ea1ae5fbea312` |
| 靜態 tree（兩次相同） | `183c90c3aed10c1bc5b76777c3efdccb19601b0b` |
| Pages來源 | `legacy`、`codex/ryu-ring-topdown-48a22f71`、`/` |
| 成功部署 | `7604129935`，2026-11-06 23:42:05（台北）回報 `success` |

## 卡住與恢復的實際證據

初次將發布包推到新分支後才選定 Pages 來源，再以 API 要求建置。原部署 `7603341219` 持續 `in_progress` 超過30分鐘，重送建置沒有解除；公開檔案仍符合前版 `81d3b3da`，不是單憑本機快取推測。倉庫 Actions 政策雖回報 enabled、workflow active，實際 dispatch 仍遭 HTTP422「Actions has been disabled for this repository」拒絕，因此沒有宣稱 Actions通過。

獨立代理複核發布包：13,846檔、185.4MiB，無異常路徑／符號連結／CNAME，`.nojekyll` 正確；相較成功前版只變更兩份JS與入口版本碼。JS與來源、canonical產物一致，語法、執行檔引用及版本雜湊均正確。Pages來源、HTTPS與環境的分支允許設定也已核對。

接著在已選定的同一發布分支上，推送一份**相同tree、零檔案差異**的前進提交，作者沿用前次成功發布的帳戶與email。新部署於23:41:42建立、23:41:50開始、23:42:05成功。沒有新增分支、改寫歷史、修改遊戲bytes或變更服務保護。

這證明正常push恢復了本次發布；尚不能證明先前API部署卡住的GitHub內部根因。先前將卡住當作正常等待、估計1–3分鐘不準，不能沿用該估計。[GitHub官方排查指引](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)亦要求核對發布來源上有具管理權限與已驗證email帳戶的push；本次email沿用成功發布身份，token沒有讀取私人email清單的權限，未額外擴權。

## 最終公開驗證

- 公開入口與八個關鍵檔案SHA256全數符合canonical發布包。
- 桌機1280、手機360及390，正常Lv1開局，再以原生選卡學會散射及Lv5圓環；四個橢圓方位目標各真正扣血428，圓環結束後動作清理正常。
- 無頁面錯誤、HTTP載入錯誤或水平溢出；受控等級與靶位不冒稱自然XP完整養成。
- canonical打包版圓環合約、既有巨砲及共用特效回歸通過。美術兩輪實看與具體退回／放行見 [美術記錄](art-review.md)。

證據：[發布與公開雜湊](qa/public-release.json)、[公開瀏覽器結果](qa/public-browser.json)。完整本機狀態、正常入口畫面與影片位於 `.omx/state/ryu-ring-topdown/` 及 `qa/presentation-v2/`；原始影片未加入公開包。

尚未驗證手機實機長局、音效、自然XP全程養成或玩家主觀自然程度。後續文件提交不改變此已發布遊戲來源。
