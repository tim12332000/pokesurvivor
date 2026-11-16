# 鹿丸單根有機影鏈發布

[遊玩此版](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=shikamaru&release=5f56fdbc)。已完成公開核對及真正開局。

遊戲來源：`5f56fdbc420a76a2b6f36b1fdde86492c49bf984`。正式靜態提交：`e15aa2da1fecb06358823157099a6789c7a4e7c9`。沿用原Pages網址、HTTPS、legacy模式，來源分支為 `codex/shikamaru-pages-5f56fdbc`；未改服務保護。

15個公開檔案逐位元組同時符合靜態提交及canonical artifact；證據為 `.omx/state/shikamaru/public-assets.json`。公開根入口在真Chrome桌機／390／360手機視窗皆能正常選鹿丸Lv1開局，素材ready=true、零pageerror；主代理另親看公開桌機單根彎影與腳底池。紀錄及截圖為 `.omx/state/shikamaru/public-browser-chain/`。沒有把push或queued當發布完成。

## 本次修正

使用者否定前版太規整、廉價與開局多條放射，要求命中A後再過渡B。本次撤回前版影形放行作本輪依據。

- Lv1只有一根活動影尖，沿固定seed的不對稱彎曲路徑爬向A；真接觸A才由A續B，再接C。
- 升階／數量增加順序接力預算，並非同時從腳底多撒影。影縫沿已成立鏈接力；移除拘束與收網時重畫的直線fan、紫色幾何線。
- 路徑、可見mesh、牆／命中與腳底池用量共源。活端點跟隨腳底、段內路徑固定；A死後用已確認contact點續接，傷害回呼取消則立即停止。
- 單根首觸恢復完整傷害；未學札縮短等待，不為展示接力而保怪命或削弱其他角色。預覽與圖示同步真連擊收益。

產品檔：`.omx/naruto-shikamaru.js`、`.omx/naruto-skills.js`、`.omx/jujutsu-growth.js`、`.omx/naruto.js`及入口。沒有新增依賴或重生成人物素材。

## 當輪證據

[總監](chain-review.md)、[美術](chain-art.md)、[合約](chain-contract.md)、[QA摘要](qa/chain/summary.json)記錄新案例與來源。六組新chain案例、有效舊控制回歸、九項標準Node檢查及相關語法／編譯通過。

正常Lv1、零永久、真鍵盤／選卡：109.24秒到Lv10，九張真卡、HP137.99存活；同cast234的budget3實際依序命中A／B／C，首次升級19.016秒。自然片前後唯一來源差異是入口資產queryhash刷新，主要runtime／skills／growth／art／metadata完全相同。近距A/B約16ms，不用停格圖冒稱每跳肉眼清楚；另有同版兩張真升階、分散三靶的同cast2原生短片及四相證可讀接力。

美術獨立看桌機／360／390入口及真播放，確認單根、穩定彎曲、不逐幀亂抖、無fan與紫直線。新verdict不沿用前版三角形分數。原始影片／完整ledger留本機，摘要含原始SHA。

未驗手機實機長局、音效聽評；使用者是否認可美感及樂趣仍由實玩判斷。保留原有無關角色報告及生成的QA報告，沒有夾入本次產品提交。
