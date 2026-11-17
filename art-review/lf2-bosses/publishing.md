# 冰火人與邪鬼：經典 LF2 首發紀錄

**前版歷史紀錄：使用者已否定省略技能的範圍，以下四招教學版本不作完整六招的完成依據。完整技能補齊由重新開啟的總監、考據、美術及測試閘門另行驗收。**

已公開：[Firzen 冰火人](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=firzen&release=15e2fa80)／[Julian 邪鬼](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=julian&release=15e2fa80)。

- 來源提交：`15e2fa80dedad3aab7a1ed239c65dd276a59ef98`。
- 正式靜態提交：`5640073776c3e8279dfcccba33503ced7a1124e8`。
- Pages來源：`codex/lf2-bosses-pages-15e2fa80`，`/`，沿用 legacy 模式、原網址與HTTPS；沒有改域名或服務保護。
- 前一來源：`codex/freeze-classic-pages-96463fd5`。

乾淨 Git checkout 產生正式包，角色／控制／音效runtime和三角metadata原始bytes均對上Git blob；原始安裝器、研究原檔與QA影片不進正式包。靜態tree保留正式包bytes，沒有讓Windows autocrlf改寫產物。來源與包推送後，標準Pages build endpoint回queued；最終以公開bytes與瀏覽器結果放行，沒有把push／queued當完成。

最終公開109個關鍵檔（入口、runtime、三位LF2角色全部PNG/WAV和metadata）與正式包逐檔SHA完全一致。Freeze、Firzen、Julian各自桌機和390手機視窗共六個全新訪客開局均為Lv1、正確起始招、素材ready，零頁面錯誤／缺失請求。Freeze另有本機完整受控回歸通過。證據在本機`.omx/state/lf2-bosses/public/bytes.json`、`browser.json`和六組截圖。

兩位各六組正式入口受控驗證通過；四份Lv1自然局以真鍵盤／觸控與實際選卡學齊各自技能，均完成招牌窗口及收束。最終原生影片、獨立原作考據與美術複核均已放行；細節見[verification.json](verification.json)、[qa/provenance.md](qa/provenance.md)、[reference.md](reference.md)及[director.md](director.md)。原素材格內4,586,787像素保留，來源SHA與重建方式記錄完整。

Firzen保留原三招與空手保底；Julian四招教學＋真跑拳／普通拳，Mirror Image的手動迴避與誘餌系統本版未移植，沒有冒充攻擊分身。自動施放、俯視投影、成長和敵人屬性為本作改編。未驗實體手機長局、多人網路與真人音效聽評；沒有將實測或視覺判定當作玩家主觀樂趣認可。

後續feature分支push不會自動更新此靜態發布來源；需以新的驗證來源重建、發布並公開核對。
