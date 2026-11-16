# 九尾化與影分身正式發布

2026-11-16 已發布並完成公開核對：[遊玩鳴人](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=naruto&release=51805cee)。

| 項目 | 最終版本 |
| --- | --- |
| 功能來源 | `3290233e414879b395a6545b88ceb0ed3fbb8746` |
| 升階修正後的發布來源 | `51805cee99285099d4d502f3531fc75b419438f5` |
| 靜態發布提交 | `154163e7135e2e0706ce83579f94b73863a3c82e` |
| Pages 來源 | `codex/naruto-cloak-pages-51805cee`，`/`，`legacy` |
| 公開版本清單 | [naruto-cloak-release.json](https://tim12332000.github.io/pokesurvivor/naruto-cloak-release.json) |

沿用原網址與 HTTPS，CNAME 仍為 null，沒有變更服務保護。使用既有 branch-hosting 路徑，更新來源後明確請求 Pages build；push、HTTP204 與 queued 都未被當作發布完成。最後以公開 bytes 及真瀏覽器結果確認。

來源只提交鳴人相關功能、圖集、註冊／打包與測試。其他角色的未提交修改保留在主工作區，沒有帶入發布。由獨立 worktree 的提交內容建置；Windows 換行差異經 Git blob bytes 核對，靜態提交與發布包一致。

## 本次發布前後修正

1. 重現「新版載入器讀到舊的、不含 directional 的 metadata」造成的素材載入失敗。metadata 與兩張圖集現在共用載入器的版本鍵，metadata 重新驗證；正常入口與舊快取反例均已通過。
2. 第一輪線上檢查發現升階引擎把 `radius` 當乘數，原本填絕對值會使最高階範圍異常放大。最終提交改為 `1.125` 與 `10/9`，並增加所有階數的精確數值斷言。這項發現已修正、重新發布並再次核對，最終版本不是第一輪候選。

## 最終公開驗證

- 13 個關鍵公開檔逐位元組 SHA256 同時符合 canonical artifact 與靜態 Git blob，包含入口、九尾化載入器、metadata、側身與正背面 PNG、分身、技能與螺旋丸特效。
- 公開根入口的桌機 1100、直式手機 390，首次及快取後重新開啟皆能正常選鳴人從 Lv1 進場；零頁面錯誤、零本站素材 HTTP 失敗。此組檢查啟用瀏覽器 service workers，沒有本機 request routing。
- 公開版本在受控 Lv9／技能一階，核對本體與影分身正背面、四向鍵盤與觸控、既有／新召出分身同步、真正拳擊與震擊、螺旋丸真實集氣／出掌的球心及遮擋、到期還原和歸屬清理。
- 桌機／手機皆跑完整原生變身窗口，確認到期與後續普通狀態；分身不重複複製震擊，牆後與範圍外不命中。
- 公開版本逐階精確檢查：半徑 `96/96/108/108/120`、震擊基傷 `18/22/22/26/32`、冷卻 `14/14/14/14/11.9`、持續時間 `8/9/9/9/10`、攻擊／移速倍率與末階間隔 `0.55`。獨立覆核以原生 `Moves.instance` 和逐次 `Moves.levelUp` 取得相同結果。
- 發布前九項標準 Node 檢查、五項素材／重現性檢查、方向／過渡／九尾生命週期、快取回歸及正式打包通過；升階修正後重驗正常入口、精確升階與相關成長契約。

本機證據集中在 `.omx/state/naruto-cloak-release/`：`release.json`、`public-assets.json`、`remote-after.json`、`public-smoke.json`、`public-directions/report.json`、`public-window/normal-report.json`，以及對應截圖／影片。公開驗證沒有攔截請求以本機檔案替換線上資產。

限制：戰鬥核對使用受控技能配置，並非 Lv1 自然選卡長局；手機為瀏覽器模擬，未測實機長局與音效。使用者對美術與爽感的判斷不由自動化代替。
