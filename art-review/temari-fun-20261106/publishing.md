# 殘風連鎖發布記錄

已發布：[遊玩手鞠](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=temari&release=0c65dd1a)。

| 項目 | 實際值 |
| --- | --- |
| 遊戲來源 | `0c65dd1a4ef9a24d2457788119810f7b9a82f20f` |
| canonical 靜態產物 | `483d8480d244b26a45db4d0087ac869187821953` |
| 前次產物 parent | `06b4699baa5232ea85e9e94aae4a08376e89c4e2` |
| Pages 來源 | `legacy`、`codex/madara-pages-c54dc3cc` 分支 `/` |

總監候選放行，未解阻擋為零；清理後 29 項完整回歸全通過。同成本／同敵人編組對照、新機制的真正自然成形、獨立美術與動漫實看已收齊。乾淨 worktree 以 `core.autocrlf=false` 建置成功；相較前次公開產物只修改七份本輪程式及入口的資產版本碼，沒有新點陣素材、依賴、影片或本機狀態。網域、HTTPS、CNAME 與服務保護維持原設定。

## 實際公開核對

- 入口、程式及 metadata 共 12 個關鍵檔案，公開原始 SHA256 全數符合產物；等待傳播完成後才判定發布成功。
- 全新桌機與 390 手機視窗正常選角、進入手鞠 Lv1；真鍵盤／觸控移動約 91.98／95.43，零頁面錯誤、HTTP 資產錯誤或回應讀取錯誤。正常畫面已實看。
- 新能力 API 實際載入，Lv1 尚未學大鐮鼬時 `enabled=false` 正確；衍生傷害別名也已載入。
- 七份修改程式均由瀏覽器實際載入，沒有靠未載入模組的額外請求替代執行證據。六份回應內容直接符合產物；VFX 的 UTF-8 BOM 被 Chrome/CDP 文字解碼移除，已分開比對其解碼內容與完整原始 HTTP bytes。
- 工作樹錄製的 CRLF hash、Git blob／canonical 的 LF hash 與瀏覽器 BOM 解碼形式分開記錄。桌機 portrait 重新導向的預載取消另列，沒有冒充 HTTP 資產失敗。

本機完整資料：`.omx/state/temari-fun/release.json`、`regressions/summary.json`、`canonical-build.log`，以及 `qa/public/public-report.json`。新玩法及檔案清單見 [implementation.md](implementation.md)；獨立放行見 [director.md](director.md)、[art.md](art.md)、[anime.md](anime.md)。

後續文件與原生採樣工具提交不改變上述公開遊戲來源。未宣稱物理手機長局、Firebase／WebRTC 真實封包遺失或真人主觀樂趣已驗證。
