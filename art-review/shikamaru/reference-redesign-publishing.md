# 鹿丸參考驅動重設：產品與發布紀錄

狀態：已完成發布。真產品已完成QA／自然核心及動漫、美術、總監獨立複查；16個公開檔案逐位元組符合正式包，公開桌機／360／390亦已真正選角並Lv1開局。沒有把prototype當成完成角色。

[正式遊玩新版鹿丸](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=shikamaru&release=86e86b9d)。遊戲來源`86e86b9d0e2e452bdd3ba463a8ca3813c0f2ee5e`，靜態提交`d5b8dec26208c93ec46c800bc724dc3ea393369f`；Pages來源`codex/shikamaru-pages-86e86b9d`，沿用原網址／HTTPS／legacy，未更動保護。正式包以舊已發布Naruto靜態提交為parent，不回退並行功能。公開SHA紀錄為root `.omx/state/shikamaru/public-assets.json`，比較正式static commit與canonical artifact，不混稱工作樹LF／CRLF的raw SHA。

## 重新設計的依據

優先採用使用者三張圖與[指定影術影片](https://www.youtube.com/watch?v=KiGKoWDE0u8)，另實際解碼檢視Crunchyroll[飛段戰](https://www.youtube.com/watch?v=c7UDaDGKGVA)及[影縫片段](https://www.youtube.com/watch?v=cu6wGFGoI7g)。[來源與時間戳](redesign-anime/references.md)區分官方、使用者指定剪輯及缺失片段，未假稱完整聽看所有影片。原始研究媒體留本機，沒有放入遊戲包。

此前的灰紋粗帶、完美圓盤、敵腳冰刺、體外浮手方案撤回。新主線為：

- **人物投影拉長**：當格頭肩／雙足alpha形成地影，窄黑前沿真接對方自己的地影後才捕捉；怪物用其原生sprite，不把怪都畫成鹿丸。
- **已捕投影融合**：由已捕者真投影與通道組成不規則掌片，留地面負空間；不強填凸包／大楔偷算AOE。被捕敵原地不動，不再跟玩家delta拖行。
- **同影鼓起高拱**：從同一腳影升起長黑弧，包含側弓／高度／前後端點；只有下降掃入當格怪物alpha才傷，最高過頭頂時不假打。四方向及小螢幕不退化成柱或敵腳冰刺。

保留ID與正確傷害／歸屬／取消管線；新池以影模仿、影縫、戰術與既有正確札機制為主。首縛舊ID相容但暫不進新池，沒有為湊五招回用未成立的舊手。未新增依賴／人物素材，也未改弱其他角色。

主要檔案為 `.omx/naruto-shikamaru.js`、`art-review/shikamaru/reference-shadow-geometry.js`、身體facade、鹿丸專屬資料／預覽、入口與打包清單。新projection、判定及渲染共用資料；簡化舊renderer假設，不保留被否定的畫法。

## 具體驗證

[QA摘要](qa/reference-redesign/summary.json)、[動漫產品複查](redesign-anime/runtime-review.md)、[總監看板](redesign-director.md)及美術實看資料各自保留來源SHA。已驗真alpha內外／當格方向與足底、同位變牆／換world快取失效、真卡接影1／2／2／3不同靶、融合後接點仍在新alpha、原地束縛、回呼hurt／onDealt同波取消、死亡／退學／換場／分身隔離、只讀繪製。

真xyz弧最高過頭頂無傷，下降接身才經原生hurt，每輪不重打；第一個1e-14 tip邊界失敗用1e-6 world EPS修正，未放大攻擊帶或放寬測試。已學影縫時舊net不搶先2x擊殺，收勢等合法活弧／波次；全靶死則不空等。

新正常Lv1真卡局（不是舊片）75.44秒到Lv7，六張真卡，HP205.61存活，融合／高拱下降真hurt／完整recover成立。第一筆新弧真傷在27.669秒：自然104號怪maxHP51、接觸前HP1，progress .953、z35.18時真alpha接身，hurt94致死；沒有補血、保怪命、改XP／敵潮／clock。正常桌機／390四向首中末、最高越身、真下降hurt與回收原生影像另存，源碼穩定。

原型body／group／sewing／首縛研究只有展示時計，與此真產品證據分開。舊巨楔與上下黑柱退回、修後C弓原生來源亦有版本區分，不用舊數據／分數替新方案放行。

## 整合與界線

獨立分支 `codex/shikamaru-reference-redesign` 工作，沒有覆寫root其他未提交檔；候選包含外部已發布Naruto／禁術卷軸提交 `bef89915`，不以鹿丸部署回退它們。遊戲碼凍結提交為 `86e86b9d0e2e452bdd3ba463a8ca3813c0f2ee5e`，自然與原生驗證來源一致；後續QA／研究文件提交不改遊戲碼。

美術已實播本輪桌機／390四向產品片至ended（10.56／9.52秒），親看正常真怪alpha、自然融合、高拱下降與左右／上下收勢；來源與SHA為`qa/reference-redesign/art-runtime-review/four-direction-playback.json`。此為當輪產品，不用原型或舊材質分數代過。

公開真Chrome三組均dex30017／Lv1／素材ready=true／零pageerror，並有真鍵盤移動截圖。主代理另親看公開桌機人物地影。結果與截圖為root `.omx/state/shikamaru/public-browser-reference-redesign/`；不是commit／push／queued就當上線。

未驗手機實機長局、音效聽評或使用者主觀美感／樂趣；不作超額宣稱。
