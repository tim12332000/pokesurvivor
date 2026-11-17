# Firen 完整四招：公開發布紀錄

已公開：[遊玩火人](https://tim12332000.github.io/pokesurvivor/.omx/digimon.html?lang=zh-TW&hero=firen&release=d3adf908)。

原版 readme 的 Fire Ball、Blaze、Inferno、Explosion 四招全部進正常學習、HUD和說明，沒有省略 named skill。火球依序原姿勢出手；Blaze依真輸入衝刺、停下收勢並留下獨立地火；Inferno從嘴部釋出獨立原火舌；Explosion保留8%最大生命成本，每次施放首段釋放時扣一次，生命不足則取消而不自動致死。原版素材、動作和資料來源見[reference.md](reference.md)。

- 來源提交：`d3adf9080ad291359f5af8901ceeff60c9f7fcab`。
- 靜態發布提交：`d8af3b60edc334b4e70c6c0bd7b0393326a88392`。
- Pages來源：`codex/firen-pages-d3adf908`，維持原網址、legacy模式及HTTPS；前來源`codex/lf2-bosses-pages-d46395d6`。
- 乾淨來源checkout建置，重要runtime/metadata bytes對上Git blob，原大安裝器、研究檔與QA影片不進正常包。

公開 **137個關鍵檔** 與正式包逐檔SHA完全相同。公開Firen全新桌機／390手機視窗各從正常選角Lv1開局，實際四個能力與四個學習圖示均核對，素材ready、零頁面錯誤／缺失請求。初次全LF2批次的首個Freeze啟動等待曾逾時，未宣稱該八入口批次通過；其後直接實際Firen入口兩種視窗均通過，沒有以queued或push當發布成功。證據在本機`.omx/state/firen/public/bytes.json`、`browser-firen.json`及截圖。

本機八組受控驗證、兩份Lv1真鍵盤／觸控自然選卡成形、當前四招原生片，以及獨立總監／考據／美術均通過；Julian完整六招另有共用接點瀏覽器回歸通過。音效／受傷施術格的純修正與當前影片差異證明見[verification.json](verification.json)及[qa/provenance.md](qa/provenance.md)。手機完成四招判定時仍為10.8HP，**影片後續尾段死亡**，保留此事實，沒有挑成功片重跑或宣稱整份影片存活。

未驗實體手機長局、多人網路與真人聲音聽評。Firen與實際Freeze的雙角色合體／分離是另行明列的配對系統，不是第五個readme招式；本輪沒有用免費Freeze幫手或單人自動Firzen假稱合體。
