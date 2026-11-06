# 純愛砲發布記錄

[遊玩乙骨](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=yuta&release=0931f9ae)。純愛砲在Lv.8選卡學習，不是開局免費技能。

| 項目 | 值 |
| --- | --- |
| 遊戲來源 | `0931f9ae7fe682a4feb80ffeae98c243d00b7d94` |
| canonical 靜態產物 | `10313fd9da0ac45ec3cecef6f4aeb8b5d670bd87` |
| 前次公開版本 | `483d8480d244b26a45db4d0087ac869187821953` |
| Pages來源 | `legacy`、`codex/yuta-love-canonical-0931f9ae` 分支 `/` |

從獨立 `core.autocrlf=false` worktree 重建，七個變更執行檔的bytes符合Git blob；七張JJK現用圖集與動漫審查版本完全一致。相較前次公開包只變動七份程式／樣式及入口版本碼，共八檔。沒有新依賴、圖集、原始錄影或本機工具進入公開包；網域、HTTPS與服務保護保留。

初次本機工作樹包混入Windows換行與舊產物，已由後續canonical產物取代，歷史未強制覆寫。Pages使用本次獨立命名的canonical分支，以免將API queued當作部署成功；最終以公開bytes及真瀏覽器驗證。

公開入口與八個關鍵檔案的原始SHA256全數符合canonical產物；本機紀錄 `.omx/state/yuta-love/publish.json`、`public-assets.json`。桌機、360及390手機視窗從正常Lv.1入口開局，再透過原生選卡學到純愛砲並自動施放；共同砲道、真正扣血與回復冷卻已核對，沒有頁面錯誤、HTTP載入錯誤或水平溢出。這段受控試招不當作自然升級長局。

完整改動、驗證與未驗範圍見 [implementation.md](implementation.md)，獨立動漫放行見 [anime-review.md](anime-review.md)。後續文件提交不改變上述公開遊戲來源。
