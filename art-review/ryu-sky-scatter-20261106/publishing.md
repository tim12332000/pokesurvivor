# 石流龍／烏鷺合併發布追蹤

後續已完成[獨立Sites外部公開發布](sites-publishing.md)；下文保留GitHub Pages受阻的實際紀錄。

程式已合併並推送到 `feat/digimon-sandbox`。本記錄建立時公開發布仍受阻，**不能將推送或in_progress視為已上線**；最終以公開bytes及兩角色瀏覽器驗證為準。

| 項目 | 已核對值 |
| --- | --- |
| 合併遊戲來源 | `190c500e583aa012b965c7c8b0e3718f554b6223` |
| 包含烏鷺來源 | `f3c3edd77668d707754c1c675660bd8ff4cb9f4e` |
| 石流龍主要實作 | `d34d0afe`，後續測試／說明在來源190c500e |
| 原始靜態提交 | `28a0d7c75dc3f3d5d319d3b44ab58d843c2690e3` |
| 同tree重試提交 | `9111df831ef6bb7fab73e7427ad12c80a68411bb` |
| 兩次相同的靜態tree | `b8667f37562d5978250839e6586a3436bc79d6c8` |
| Pages來源 | 原有`legacy`、`codex/ryu-ring-topdown-48a22f71`、`/` |
| 原部署 | `7604870368`，台北2026-11-07 00:15:03建立、00:18:02進入in_progress |
| 同tree重試部署 | `7605128837`，台北2026-11-07 00:26:34建立、00:32:17進入in_progress |

最初以原子push同步來源主分支與原有發布分支；未更換Pages設定，也未建立新發布分支。超過十分鐘仍未更新公開內容後，僅對已選定發布分支補推相同tree的新提交。這是恢復嘗試，不能據此斷定GitHub內部根因。

獨立發布稽核確認：185.42MiB／13,846檔，`.nojekyll`、無CNAME、無符號連結、本機工具／狀態排除、入口引用與版本雜湊均正確；八份執行檔bytes符合合併來源。與前次公開包只差七份Ryu相關JS及入口版本碼，烏鷺runtime blob完全相同。來源分支、作者／提交者身份及環境分支允許規則也已重新核對，沒有更動服務保護。

最後核對時，公開入口及烏鷺runtime符合，Ryu與其共用資料／特效仍回傳舊版bytes。兩次Pages任務沒有成功／失敗細節。備援workflow實際dispatch仍遭HTTP422「Actions has been disabled for this repository」拒絕；沒有宣稱hosted Actions通過。

## 已通過而不等同公開成功的證據

- 烏鷺與石流龍的來源祖先均存在於`feat/digimon-sandbox`，遠端主分支已是190c500e。
- 合併版Ryu散射／巨砲／角色回歸、烏鷺繞彈、九項Node檢查、42個成長合約、語法及diff檢查通過。
- 最終桌機／360／390共48張相位畫面、6支原生短片，美術獨立實看通過；詳見[實作記錄](implementation.md)與[美術記錄](art-review.md)。
- 真正打包後的散射合約與共用特效回歸通過。另從打包版正常桌機入口驗證原生自動施放：Ryu八發打中760距離目標，Uro繞彈0.8秒後回射，無頁面／HTTP錯誤。

內測：[本機石流龍](http://127.0.0.1:8337/.omx/digimon.html?lang=zh-TW&hero=ryu&release=190c500e)；僅此電腦。已核對本機Ryu執行檔符合合併產物，沒有將內測冒稱公開版。

可恢復的發布資料保留在製作worktree `.omx/state/ryu-sky-scatter/publish.json`、`public-assets.json`。`publish.py verify`核對十個公開檔案；只有全部符合後，`browser_public.py`才核對公開Ryu／Uro各桌機／360／390的正常Lv1開局、合法學招、自動施放與真正命中／繞彈。這些公開驗證尚未完成時，不應寫成已部署。

未驗手機實機長局、音效及自然XP完整養成。發布工作之外未新增依賴、重寫歷史或調整服務保護。

