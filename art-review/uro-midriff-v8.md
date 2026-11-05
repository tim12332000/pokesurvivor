# 烏鷺腹部與分離空間遮蔽 v8

版本：`sendai-20261106-space-midriff-v8`。

使用者指出v7的「肚子呢？」後，已撤回寬幅胸腹遮蔽的造型通過結論。動漫、美術及共同品質指引改成必要條件：普通腹部正常可見，胸前／腰胯的光學遮蔽分離，不再把範圍較寬當成可接受交付。

## 素材與實作

- 使用內建 `imagegen`，只編輯原本完整穿衣的遊戲圖集，產出成年角色穿不透明短上衣／短褲、普通腹部可見的安全底圖。沒有輸入裸露官方參考，沒有用程式重建皮膚或私密細節。兩張原始輸出另存，未覆寫v2。
- 原始輸出：`uro-space-v8/uro-common-source-v3.png`、`uro-space-v8/uro-skills-source-v3.png`。提示集為同目錄 `prompts.json`、`skills-prompt.json`；來源與runtime SHA256在 `provenance.json`，兩組皆逐位元組相等。
- 正式素材：`redrawn/jjk-uro-common-v3.png`、`redrawn/jjk-uro-skills-v3.png`。`.omx/jujutsu-art.js`保留真素材的腹部／肚臍，只將上下服裝區轉成環境取樣與空間折移；鄰近服裝的黑色下襬／褲腳不再被膚色保護誤還原。
- `jjk-skills-v2.json`只更換Uro的兩張sheet；其他角色sheet、rect、anchor與所有animation dispatch保持相等。`tools/build_jujutsu_v2_assets.py`提供v3來源／runtime登記規則，全部七張sheet只讀重算與metadata一致。
- loader新增JSON版本query `?v=uro-midriff-v8`，新PNG也使用新檔名，避免已玩v7的瀏覽器留在舊資料。

底圖的安全服裝不是最終造型：正常遊戲與選角預覽使用同一光學遮蔽流程，腹部保持原像素，遮蔽區呼應環境。彎身／受傷時原動作自然遮腹，不強改姿勢硬露出。

## 驗證

- `.omx/state/uro-space-body/v8/report.json`：桌機／390px手機、24圖格與鏡射共48姿勢、UI、低畫質、白閃／分身透明、快照預算、換草／土／圖案背景，以及鍵盤／觸控與分身原生片。
- `.omx/state/uro-space-body/v8-hem/`：先在舊renderer配相同v3素材重現衣物黑緣誤還原，再驗修正後衣緣跨背景改變、腹部原色保留；沒有以膚色填色掩蓋問題。
- `.omx/state/uro-space-body/v8/uro-v8-renderer-closeup.png`為正式renderer的QA放大圖，不是另外重畫或身體合成。
- `.omx/state/uro-space-review/v8-review.json`：獨立實看新素材、48姿勢、正常入口、UI、材質、原生動作與分身，以及最後衣緣修正；`final_v8_pass_after_hem_cleanup`，阻擋項為空。v7撤回結論保留。
- 八項現行CI Node檢查、JS語法、Python編譯、diff與生成器可重現性核對；打包後三角色桌機／手機學招、真輸入、傷害及生命週期在 `.omx/state/uro-space-release-v8/built-entry/`。

本輪沒有改技能傷害、冷卻、角色ID或存檔。沿用現有圖集／分派和光學快照，未增加依賴。正常尺寸與放大圖都實看；不把機制測試或視覺分數等同玩家滿意。實體手機長局／熱降頻、真人連線仍未驗。
