# 鹿丸技能辨識發布

[遊玩此版](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=shikamaru&release=11149aee)。已完成公開核對及真開局。

來源 `11149aee0913b71e8d7f3297cf1d03d296858576`；靜態提交 `b31ddf81eeeb24782c3e995a819f21a213178fb4`。Pages來源 `codex/shikamaru-pages-11149aee`，沿用原網址／HTTPS／legacy，沒有變更服務保護。

15個公開檔案逐位元組同時符合靜態提交與canonical artifact；逐檔SHA位於 `.omx/state/shikamaru/public-assets.json`。真Chrome從公開根入口，在桌機及360／390手機視窗皆正常選鹿丸Lv1開局、素材ready=true、零pageerror；主代理另實看公開390畫面。紀錄及截圖為 `.omx/state/shikamaru/public-browser-identity/`。push及queued沒有被當作發布成功。

## 差異與保留

- **影模仿**維持貼地單根ABC與纏足，仍會拖帶已捕者；腳底池保留真用量縮放。
- **影縫**從捕捉點逐波升起高刺，真傷害當格達尖峰，然後沉回。每cast／target只有一組刺actor，不再每pulse新生一組疊成森林；本體有一次真施術低蹲／起印窗口。
- **影首縛**首次傷害前由腳沿身上升，之後同一手臂逐段收緊，不反覆重播升手；頸位取真bodyH。
- **收網**只做地面交叉束環與站立收束，與穿刺、盤身不同。後續合法影縫接力另有真事件，沒有把刺誤稱net。
- HUD與世界提示讀實際cast／actor，不在出影縫時仍顯示等待、不在無真首縛時假演終結。

主要改 `.omx/naruto-shikamaru.js`、`art-review/shikamaru-art.js`及入口；重用既有身體素材。簡化跨pulse重複視效物件，沒有新增依賴，沒有改傷害、成長、ABC路徑、影池或札機制。

## 驗證

[美術合約與實看](skill-identity-art.md)、[QA摘要](qa/skill-identity/summary.json)記真相位／來源。六組新辨識／安全案例、phase回歸、九個標準Node檢查及相關語法／編譯通過。

49次原生hurt對49次真接觸；25個cast-target視覺組各只有一個物件；影縫真命中峰值實際69px、之後收回；首縛三pulse手指close為.8/.9/1、progress維持1不重升。render/query100次不推sim，pause／clear／死亡／換場與同wave回呼取消均驗。net原缺事件metadata的反例保留後修正，沒有放寬測試掩錯。

當輪同配置桌機／360／390各20張首中末、rise及消散與短原生影片，來源穩定；美術親看最新三尺寸播放至末。手機可辨立刺與沿身單手，未宣稱小尺寸可數清四指。未重拍無關自然長局，不用舊三角／ABC分數回應本次辨識問題。

未驗手機實機長局及音效聽評；使用者是否認可美感及樂趣仍待實玩。原有無關角色報告與生成QA報告留原狀，沒有混入產品提交。
