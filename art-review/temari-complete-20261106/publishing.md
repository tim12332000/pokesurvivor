# 手鞠整體優化發布記錄

已發布：[遊玩手鞠](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=temari&release=2f3eeb06)。

| 項目 | 實際值 |
| --- | --- |
| 遊戲來源 | `2f3eeb06e86b3495a9b1e1e0e291cbe1ac63e97b` |
| 靜態發布產物 | `06b4699baa5232ea85e9e94aae4a08376e89c4e2` |
| 前次產物 parent | `04f432d3c30008ff235170fe6cd572905171be93` |
| Pages 來源 | `legacy`，`codex/madara-pages-c54dc3cc` 分支 `/` |
| 網域／HTTPS | 沿用原網址，HTTPS 啟用，CNAME 為 null |

總監產品候選放行，未解阻擋為零。限定清理後 **25 項完整檢查全數通過**，包含九項標準 Node 檢查及十六套角色／聯機／風效回歸。從乾淨 canonical worktree 建置成功；相較前次公開產物只變更七份本輪程式及入口的七個資產版本碼。沒有帶入本機測試狀態、原始影片或未追蹤研究素材，沒有變更域名或服務保護。

## 公開核對

- 入口及關鍵程式／metadata 共 12 檔，公開原始 bytes 的 SHA256 全數符合產物。
- 全新桌機及 390 手機視窗，正常選角進入手鞠 Lv1；實際鍵盤移動約 89.81、觸控約 96.54，零頁面錯誤、零 HTTP 資產錯誤，畫面已實看。
- 七份修改程式均在瀏覽器實際載入。六份瀏覽器回應內容直接符合產物；VFX 含 UTF-8 BOM，Chrome/CDP 的文字回應會移除 BOM，已分開驗證其解碼內容及同一公開 URL 的原始 HTTP bytes，沒有把不同位元組形式混稱相同。
- Windows 工作樹的 CRLF 錄製 hash 與 Git blob／canonical 產物 hash 分開記錄；公開比較對象是實際產物。
- 首次冷載入超過原測試的 30 秒素材等待，延長觀察後真正載入並完成開局。沒有為通過驗收改產品或略過素材準備；原診斷保留。桌機 portrait 重新導向的預載取消也有獨立記錄。

本機完整資料：`.omx/state/temari-complete/release.json`、`regressions/summary.json`、`canonical-build.log`，以及 `qa/public/public-report.json`。候選自然養成與獨立驗收見 [implementation.md](implementation.md)、[director.md](director.md)、[art.md](art.md)、[anime.md](anime.md)。

沒有宣稱實體手機長局、真網際網路 WebRTC 遺失情境或玩家主觀樂趣已被自動化證明。後續文件提交不改變以上公開遊戲來源提交；原 Pages 分支名稱保留歷史命名。
