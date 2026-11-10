# 斑連續演舞與蓄力末斬發布記錄

2026-11-11：[遊玩新版宇智波斑](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=madara&release=5da2919f)。

- 遊戲來源：`5da2919fad1c12ad5a045c829d0a06cd8d874bf3`。
- 靜態發布提交：`b3028d5a844e1ce05437b3c58b77c7e2f2a7f17a`，parent `47d06ed1604d61f38b99bc74a5612383a0ea8653`。
- 當次查核 Pages 為 legacy，來源 `codex/ryu-ring-topdown-48a22f71`、路徑 `/`。保留既有 HTTPS、網址及 CNAME=null。
- 從來源提交以 LF canonical worktree 執行九項標準 Node 檢查及正式產生器，再把新版 `.omx/naruto-madara.js` 與只更新該腳本版本的 `.omx/digimon.html` 疊入現行公開 tree；其他公開檔案未改動。
- 來源與靜態分支 atomic push 成功後，另外要求 Pages build；queued 不作成功依據。公開入口、loader、斑戰鬥、繪製、metadata 與鏡頭六項 SHA256 已逐一與發布 tree 核對相同。
- 公開版本18項演舞／閃避／木分身回歸及7項末斬測試全部通過，未覆寫來源提交中的本機 QA 報告。
- 公開網址桌機1280、手機390／360皆從正常Lv1選角開局，基本演舞與兩名木分身實際載入；桌機鍵盤及手機觸控移動通過。三種視窗均零JavaScript錯誤、零HTTP缺檔、無水平溢出。
- 線上實際資料核對：豪火18秒、須佐30秒、落石52秒、木分身36秒；完成體末斬蓄力5秒，演舞閃避80%，木分身協戰6秒且至少休息12秒。

來源工作樹 SHA `0d50517a002d854c0a11d918b8a07630c0655ead09d5a5da60b67e613c9dc854` 使用 CRLF；公開／Git blob SHA `ccb79770bca46059d5e3ca1aafae3bd07375aa44e9b813a8a1bacd704e61fa67` 使用 LF，已確認正規化後程式完全相同。

完整發布記錄、公開雜湊、戰鬥驗證與桌機／手機正常開局證據留在本機 `.omx/state/madara-pursuit-release/`。後續發布先重新查詢當時的 Pages 來源，不能只推開發分支就宣稱上線。本輪未驗手機實機長局、完整自然成長平衡或音效聽評。
