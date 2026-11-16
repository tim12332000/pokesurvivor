# 自身尖影與移動連接：發布完成

[正式遊玩鹿丸](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=shikamaru&release=f2d1a760)

使用者最後指示已接入並發布：一般影線移動時整根平滑轉向，不留長直線接舊路徑的硬折；大捕縛改自身起手位置向外、每個敵人獨立直尖影，真正穿過身體遠側後才拘束，再投一顆低傷炸彈。圓底只保留很淺的柔邊提示。既有詰將保留，沒有重做其設計。

| 項目 | 當次真實值 |
| --- | --- |
| 遊戲來源 | `f2d1a760a37098e64e9bfeeb974f4a2fe1aeb5e6` |
| 靜態發布 | `ddae37a34a8781885e451aac8ff08aae74ba6dec` |
| Pages來源 | `codex/shikamaru-shadow-motion-pages-f2d1a760`，`/`，`legacy` |
| 原靜態parent | `f3566b4855129b6e39699703877b99c39901d8a3` |
| 網址／保護 | 沿用原 GitHub Pages 網址，HTTPS=true，CNAME=null；未改 default main 或服務保護 |

從乾淨來源 checkout 建置，現行九個標準 Node 檢查通過。與目前線上 13,853 個檔案逐 blob 比對，保留無關資產與歷史 manifest 的原 bytes。此次靜態差異只有鹿丸七個 runtime／入口檔及本輪 manifest，沒有回退其他線上功能。LF／CRLF 差異以 canonical artifact／Git blob／公開 bytes 分開驗證。

公開 [release manifest](https://tim12332000.github.io/pokesurvivor/shikamaru-shadow-motion-release.json) 與共 **20** 個核對檔案逐位元組符合靜態提交與 canonical artifact。已從公開根入口以全新桌機與390手機視窗、冷／暖快取，真正選鹿丸並 Lv1 開局、自然命中、真鍵盤移動。公開程式另通過移動曲線／繞行／重疊／牆阻，以及300敵逐人尖影、先穿身後拘束、先綁再丟、低傷單爆、32秒基礎CD、生命週期與回呼取消。零 pageerror／缺失請求；沒有攔截或替換公開程式。沒有把 push 或 queued 當作發布完成。

本機驗證另有正常 Lv1→Lv6 真選卡、主玩家第一發真爆傷並完整解除；18靶原生桌機／360／390多階段演出及獨立實看。柔邊提示的透明畫布 alpha 實測中段9/255、近邊1/255。見 [大捕縛改動與測試](mass-possession.md)、[移動曲線修正](shadow-motion.md)。

當次完整記錄保存在 `.omx/state/shikamaru-shadow-motion-release/` 的 `release.json`、`static-artifact.json`、`preserved-eol.json`、`public-assets.json`、`public-browser.json` 與 `remote-after.json`。一般工作區原有三份無關 QA 髒檔保留，未帶入提交／發布。

未驗手機實機長局、音效聽評及合作 guest 同步；自動化不替代使用者的主觀手感與美感判斷。
