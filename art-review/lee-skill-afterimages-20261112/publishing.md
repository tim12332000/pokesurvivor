# 小李與斑殘影發布

2026-11-12：[小李](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=lee&release=b934b7f4)／[宇智波斑](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=madara&release=b934b7f4)。

- 遊戲來源提交：`b934b7f490e7ff2560eef4ca63f3336203c900b6`。
- 靜態發布提交：`670e5fc6c5e74adcadce4654c5bb99b4ab0e639e`，parent `f33cfd81dbb54208ef9578687b546c8b2462fb28`。
- 實際查核 Pages 仍為 legacy、來源 `codex/ryu-ring-topdown-48a22f71`、路徑 `/`；保留 HTTPS、網址與 CNAME=null。
- 從乾淨 canonical worktree 建置，九項標準 Node 檢查全通過。發布 tree 只改 `.omx/naruto-gates.js`、`.omx/naruto-madara.js` 與這兩檔的 loader 版本，其他公開檔案保留。
- 來源／靜態分支 atomic push 後要求 Pages build。公開入口、loader、兩個戰鬥模組、斑的繪製／metadata／鏡頭共七項 SHA256 與 artifact 完全相同。
- 37組公開戰鬥／殘影驗證全部通過（斑23、完成體末斬7、小李7）。小李的比較基準固定為8edbb632，只有基準八門模組被替換，候選完整使用公開版本。
- 兩角各自的桌機1280、手機390／360共六種正常Lv1開局與原生鍵盤／觸控移動皆通過；每種畫面均核對兩份模組雜湊，零JS錯誤、零HTTP缺檔與水平溢出。主代理另實看公開小李手機390開局。

本版包含小李未開門的五種高速招式殘影，以及斑演舞同敵三次真命中再換人、人物殘影；維持演舞快速低傷害、80%閃避、既有CD、木分身出場窗口與五秒蓄力末斬。角色原生素材、歷史位置及旋轉沿用原有實作。

公開模組使用 LF，已確認與 CRLF 測試工作樹正規化後完全一致：

- 斑：`66d419b7f421d372d4b85bfb4b952c021c864b7fdebedc11807ddd78dd936d1a`。
- 小李殘影／八門：`7dd727fe6456fa7d8782f2a9597e61e9257a34eb09c2d7f53a6bb3ce3c10334f`。

完整發布工具、公開檔案雜湊、實際開局及戰鬥驗證保存在本機 `.omx/state/lee-madara-afterimages-release/`。未驗手機實機長局、完整自然成長平衡或音效聽評。
