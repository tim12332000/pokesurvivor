# 須佐軍團／豪火新版發布

2026-11-08，依使用者「直接發佈」授權，已在原網址發布：

[遊玩新版斑](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=madara&release=d1d45c4b)

- 遊戲來源：`d1d45c4bb99a8a35cc42cfb74f3dc424eebd9a36`，已推送`codex/madara-legion-d1d45c4b`。
- 靜態發布：`47d06ed1604d61f38b99bc74a5612383a0ea8653`，父版本為當時線上`0ba237e8094b435286c3b5a3504747e81c2c77ff`。
- 實查Pages來源：既有`codex/ryu-ring-topdown-48a22f71`、路徑`/`、legacy。直接快轉同一分支，沒有切換Pages來源、網址、網域或服務保護設定。
- 僅更新`.omx/naruto-madara.js`、`.omx/naruto.js`、`.omx/naruto-en.js`、`art-review/madara/runtime.js`及`.omx/digimon.html`四個資產版本號。其他線上檔案保留原tree；`.nojekyll`保留，CNAME不存在。

乾淨Git checkout使用LF canonical bytes，正式產生器成功；四個程式的checkout／Git blob／正式包逐一相同。當前線上metadata和14張圖集均與來源完全一致才允許覆寫程式。Windows工作樹raw SHA與Git canonical SHA分開核對，沒有把換行差異誤報成程式差異。

發布後公開21個關鍵檔案（入口、四模組、metadata、圖集等）全部SHA256符合發布tree。全新公開桌機／360觸控正常Lv1開局均為v3、兩名木分身，火遁Lv2／須佐Lv3／完成體二階規則正確；真鍵盤／觸控測試無JS錯誤或缺失請求。另直接於公開正常入口建立明示受控r1/Q0試招，四面新版豪火實際繪製正常。

證據位於本機`.omx/state/madara-publish-20261108/release.json`、`public-assets.json`、`public-browser.json`及相應桌機／手機截圖。瀏覽器證據不是實體手機長局，也未重新宣稱主觀好玩或聽評音色。
