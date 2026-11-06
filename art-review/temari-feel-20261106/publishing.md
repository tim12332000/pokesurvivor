# 手鞠追擊改善發布記錄

遊玩：[手鞠](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=temari&release=c62b528e)。

- 遊戲來源：`c62b528e83af35a51d6170657c28523d1a367271`。
- 正式靜態包：`04f432d3c30008ff235170fe6cd572905171be93`。
- Pages 維持 `legacy`、`codex/madara-pages-c54dc3cc` 分支 `/`；分支名稱保留歷史命名，本次已以前次 artifact 為 parent 快轉更新。沒有更動網域、HTTPS 或服務保護。
- 從獨立乾淨 worktree 以 `core.autocrlf=false` 建置，公開包相較前次只改手鞠戰鬥、中英文技能說明及入口三個資產版本碼。沒有夾入本機未追蹤素材、測試狀態或原始影片。
- 入口及八個關鍵資產的公開 SHA256 全數符合 artifact；不是只以 push／queued 判斷發布完成。
- 正常桌機及 390 手機視窗從公開根網址選手鞠、Lv1 開局、實際鍵盤／觸控移動；三個修改過的 JS 在瀏覽器中的回應內容亦符合 artifact。

原始公開核對資料：本機 `.omx/state/temari-feel-release/release.json`、`qa/public-report.json`；角色改動及驗證限制見 [implementation.md](implementation.md)。來源工作分支後續若增加本發布記錄等文件提交，以上遊戲來源提交仍是公開包的實際建置依據。
