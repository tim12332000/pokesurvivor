# 鹿丸固定投影／多重捕捉／苦無連投發布

2026-11-16 已發布並完成公開驗證。[遊玩新版鹿丸](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=shikamaru&release=e77a4cac)。

| 項目 | 版本 |
| --- | --- |
| 遊戲來源提交 | `e77a4cac8904ba8c7ac3314585abf8551ebcbfbb` |
| 靜態發布提交 | `f3566b4855129b6e39699703877b99c39901d8a3` |
| Pages來源 | `codex/shikamaru-parallel-pages-e77a4cac`，`/`，`legacy` |
| 前一靜態版本 | `d5b8dec26208c93ec46c800bc724dc3ea393369f` |
| 公開版本清單 | [shikamaru-parallel-release.json](https://tim12332000.github.io/pokesurvivor/shikamaru-parallel-release.json) |

沿用原網址及HTTPS，CNAME仍為null，未變更服務保護。來源只提交鹿丸相關程式、說明、成長預覽、測試與證據；其他未提交改動保留。沿用專案角色技能的單招驗證與既有Pages發布流程。

## 發布與變更邊界

從已提交來源建立獨立canonical工作樹，以現行產生器建置。既有178份文字只有LF／CRLF差異，核對內容等價後保留原線上位元組，再重算入口快取鍵；不是以不同換行雜湊誤判產品更新。

靜態提交相對前一線上版本恰好改7個檔案：`.omx/naruto-shikamaru.js`、`art-review/shikamaru/reference-shadow-geometry.js`、`.omx/naruto-skills.js`、`.omx/naruto.js`、`.omx/jujutsu-growth.js`、`.omx/digimon.html`及本次版本清單。其餘公開資產保持前一版本位元組。

已推送來源與發布分支、更新Pages來源及明確請求build。build-history仍回404，沒有用queued代表部署完成；最終以公開bytes、目前Pages設定與真瀏覽器核對為準。

## 線上實際驗證

- 公開版本清單及18個關鍵檔案的SHA256皆符合canonical artifact與靜態Git blob，包含鹿丸戰鬥、幾何、素材、說明、成長預覽、入口及鳴人既有關鍵資產。
- Chrome從公開根入口開啟，桌機1100與手機390、首次與快取重開均真正選鹿丸並Lv1進場；載入的是本次內容雜湊的戰鬥及幾何程式。
- 安裝受控測試前，各正常原生世界均已出現苦無掃掠命中；沒有先覆寫World才宣稱正常戰鬥成立。
- 同一公開程式的受控測試，桌機／手機均確認：瞄準改向不改投影矩陣；三條影子從本體各自出發；捕捉當下無瞬間傷害；三目標各真實命中4枚苦無。
- 上限16目標各5枚共80筆傷害；死亡分支互不連坐，移開與牆可使苦無落空；暫停、死亡、換世界、退學、clear及hurt／onDealt取消後不補打均通過。
- 首輪曾有既有怪物圖片HTTP503；未忽略該失敗，重新跑完整桌機／手機冷暖入口與行為測試後通過。最終一輪零頁面錯誤、零本站素材失敗，未攔截或替換線上請求。
- 主代理實看公開桌機／390截圖，可見獨立影子、固定光向投影與在途苦無。

標準九項Node、幾何效能測試及五個修改JS語法檢查通過。100次移動投影只需一次來源動畫格像素讀取，投影移動與接觸不逐像素掃描。

完整本機證據位於 `.omx/state/shikamaru-parallel-release/`：`release.json`、`static-artifact.json`、`public-assets.json`、`remote-after.json`、`public-browser.json`、`completion.json`及公開截圖。測試與本機證據見[驗證紀錄](qa/parallel-kunai/verification.md)。

限制：受控技能配置與短原生正常局，不代表完整自然養成、手機實機長局性能、音效或玩家主觀樂趣驗收。
