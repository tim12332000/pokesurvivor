# 戰場演舞加速版發布

2026-11-12：[遊玩加速版宇智波斑](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=madara&release=9e3c627b)。

- 遊戲來源：`9e3c627b163ecdb4b557475bbdf855a6a7913a99`。
- 靜態發布：`f33cfd81dbb54208ef9578687b546c8b2462fb28`，parent `b3028d5a844e1ce05437b3c58b77c7e2f2a7f17a`。
- 當次查核仍為 legacy Pages，來源 `codex/ryu-ring-topdown-48a22f71`、路徑 `/`；沿用原網址、HTTPS 和 CNAME=null。
- 從乾淨 canonical worktree 建置，九項標準 Node 檢查通過。發布差異僅 `.omx/naruto-madara.js` 和該檔的 loader 版本，其他公開檔案全部保留。
- 來源／靜態分支 atomic push 後，要求 Pages build。公開入口、loader、斑戰鬥、繪製、metadata 和鏡頭六個關鍵檔案 SHA256 全部與 artifact 相同；不是僅以 queued 或 push 判斷成功。
- 公開 runtime SHA：`d48950495b9f39c75297135010459de2bfa405227ba61d4fc7bc2ca73c51344f`。測試工作樹採 CRLF，已核對與 canonical LF 正規化後完全相同。
- 線上25項戰鬥回歸（演舞18／末斬7）全通過。桌機1280、手機390／360正常Lv1開局與原生鍵盤／觸控移動通過，零JS錯誤、零HTTP缺檔、無水平溢出；實際載入的傷害、時間與程式雜湊均符合此版。

本版演舞每段0.15秒、後段最短0.075秒，單段基礎傷害16；各階段數與數量上限保留。其他招式CD、80%閃避、撤退取消和5秒蓄力末斬保留。

發布工具、公開雜湊、正常開局與戰鬥回歸證據留於本機 `.omx/state/madara-combo-fast-release/`。未驗手機實機長局、完整自然成長平衡或音效聽評。
