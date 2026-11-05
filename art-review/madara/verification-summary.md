# 宇智波斑獨立驗收

2026-11-06。測試作者與戰鬥作者分離；未修改產品程式。使用正常入口 `http://127.0.0.1:8347/.omx/digimon.html?lang=zh-TW`，Python Playwright／Chrome。

最終結果：`verification-release/report.json` 為 `ok=true`，桌機1280×900、390×844、360×800全部完成；`errors`、`missing`、`failures` 均為空，產品SHA256測前／測後一致。`verification-low/report.json` 明確360px、`quality=low`、`fx=0`，亦為 `ok=true` 且三欄均空。

## 真行為證據

- 正常選角／開局、Lv1/3/6/9/12門檻、合法卡學招、所有既有跨界角色技能池隔離；前局Lv30且強制 `startMoves=2`，四次原生重開均只有Lv1起始招，無隨機第二招越級。
- 體術／火遁／須佐／隕石每招三個範圍內目標與一個範圍外目標；各段獨立hurt、來源／技能ID、牆遮擋、無敵人時原生可破壞箱子、同波prop取消。
- hurt與onDealt回呼各自clear／退學時，同波第二目標與後續段不補打；死亡、換world、run epoch、暫停；移動本體、移動敵人、stale grid活敵移除、同波移除下一活敵與擴散外圈移除。
- 火遁前三張真數量卡的真波次為4→5→6→7；三張數量後，四張合法升階卡的即時預覽為7→9、9→11、11→13、13→15，升至16波上限後不再供無效數量卡。large-dt兩次update不掉段或重複命中。
- 木分身與自身分身卡分開測：獨立位置／cast ID／wood-clone歸屬、退學停止傷害、模組單owner clear隔離。相同rank1須佐、數量0、相同敵人，以真卡升木分身rank1至5，首擊raw為144.144／172.9728／209.0088／252.252／302.7024，對應敵HP損失144／173／209／252／303；rank2、4即使人數不變仍真增傷。
- 雙隕石固定落點、兩次獨立落地再四次衝擊；移動離開落點不追打。playing／paused／levelup渲染各48883有效像素，繪製與暫停update均不改時鐘／段數／HP，恢復後正常第一擊。levelup項目是同步渲染狀態覆寫，不是自然升級流程實錄。
- `node tools/test_combat_pulse.cjs` 通過舊無guard語義及新cast.targetIsLegal：primary／secondary前重查、stale outer、回呼移除下一目標、未落地primary不產生較大幽靈擴散。

## 畫面與原生片

`verification-final/report.json` 為 `ok=true`、三視窗零錯誤，保存rank1／數量0與受控rank5／數量4的豪火首末波、須佐首末刀、兩顆隕石下降／接觸／消散、木分身顯現／攻擊／退場相位。

同目錄三份 `*-native-rank1-legal-kit.webm` 使用原生RAF錄18秒，自動施放且無直接cast／手動技能時間推進；Lv12合法學五招，技能rank1、數量0，移動敵人fixture，桌機真鍵盤／手機真CDP觸控。桌機觀察施放次數：體術10、豪火3、須佐3、隕石2、木分身1。此為受控合法配裝驗證，未宣稱由Lv1自然生存養成，也不是玩家主觀樂趣證明。

影片與相位完成後的最後產品變更為即時升階卡預覽，以及刪除一個行末空白的純格式修正。故最新文案／產品雜湊以 `verification-release/report.json` 為準，原生戰鬥與渲染證據沿用 `verification-final`，沒有為純文案或格式重拍整套。低畫質相位在 `verification-low`；其 `presentation-report.json` 保留文案／入口hash更新前的相位紀錄，同目錄 `report.json` 為文案完成後的低畫質機械驗收（早於最後純格式修正），皆不影響戰鬥／渲染結果。

## 發布對照SHA256

| 檔案 | 最終SHA256 |
| --- | --- |
| `.omx/naruto-madara.js` | `02853c81e0255f496c161a63dcb33d29a97d1765ae104aefee2085fd2ab6fc77` |
| `.omx/combat-pulse.js` | `9570100a9eb0de13a9092aa80538949201cc5fe06c3d053f5928e84ec4790b55` |
| `art-review/madara/runtime.js` | `bfd75a32138ca0bdeaac5c8c598e4fa1a42324417283b89e3cb936678af9482d` |
| `art-review/madara/madara-actions-v1.png` | `8ae1d43e099ced737b3cf3fca8184b066a8bb06eff572cb731ecee5ef69adace` |
| `.omx/digimon.html` | `5de403379bbb217987f9f4b393eb70d24d1cfd57fa6f7a8962913bbbb081499a` |

未驗：實體手機長局、真人主觀樂趣／兩流派平衡、聲音音色聽評。美術與動漫的獨立實看由對應agent另存報告。
