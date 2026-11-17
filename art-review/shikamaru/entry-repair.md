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
