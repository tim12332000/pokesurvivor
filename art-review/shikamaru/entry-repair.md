# 外部版本導電招式漏載修復

2026-11-17再次核對時，公開站已更新至火人來源 `codex/firen-pages-d3adf908`，靜態head `d8af3b60edc334b4e70c6c0bd7b0393326a88392`。鹿丸導電程式、卡牌資料和素材仍在且符合最新來源，但HTML入口沒有載入 `.omx/naruto-shikamaru-mass.js`，因此學到卡後也沒有本招的自動施放接線。

根因是 `.omx/make_digimon.py` 仍只產生舊的geometry及Shikamaru主模組；後續重產入口時，把導電版先前加入的script漏掉。打包器有複製runtime檔案，卻無法代表瀏覽器真正執行了它。

修正四檔：

- `.omx/make_digimon.py`：依序產生geometry、主模組、大捕縛導電模組，皆在main之前。
- `.omx/digimon.html`：由修正後生成器重產，產品差異只有補回一個script。
- `tools/test_catalog_boundary.js`：必跑回歸驗證四個必要腳本恰好各一次且順序正確。修前先重現 `0 !== 1` 的缺載失敗，修後通過。
- `tools/build_digimon_site.py`：打包入口同樣檢查缺載、重複與順序，不允許再產生「有檔案、沒執行」的正式包。

沒有修改招式數值、導電／炸彈演出或其他角色。本機正常入口的原生自動施放在桌機、360、390手機視窗均完成穿刺、導電、投彈、爆破與解除；不是只直接呼叫cast。九個標準Node檢查、Python編譯與diff檢查通過。

發布必須以當時真實線上火人靜態head為parent，只更新入口及本輪manifest，保留其他角色資產和LF2的metadata快取參數。正式結果在完成公開bytes及瀏覽器施放核對後補記。

## 正式站已修復

[正式版鹿丸](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=shikamaru&release=f6d40787)

來源 `f6d407877c977f59e5c7d37c1579c6b9b40725b3`，靜態提交 `6df23b58042a914cd4363b216aba87f38dcc3dc5`，Pages來源 `codex/shikamaru-entry-pages-f6d40787:/`。公開差異僅HTML入口及本輪manifest；其餘13,981個既有公開檔案、LF2腳本及metadata快取參數維持原樣。網址、HTTPS、CNAME與服務保護未改。

公開28個檔案與canonical／Git blob一致。桌機及390手機的冷／暖快取正常Lv1入口、真按鍵移動通過；另在各自的正式頁面真正自動施放一整發18靶技能，各得到18根影線、54次電擊與18次炸彈命中，完整跑到解除。沒有攔截或替換公開程式，也不只靠直接呼叫cast宣稱能出招。

首輪施放驗證均通過，但一張未改動的寶可夢倒地PNG短暫回503；重新抓取為200且bytes符合canonical，完整乾淨重測無pageerror或失敗請求。證據為 `.omx/state/shikamaru-entry-repair/{release,public-assets,public-browser,verification}.json`，首輪失敗紀錄另保存。手機實機長局仍未驗。
