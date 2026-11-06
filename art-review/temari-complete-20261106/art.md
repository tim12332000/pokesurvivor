# 手鞠整體優化：美術／VFX契約

目前階段：有界VFX、回歸與原生畫面驗收已完成。已有鐮多利追擊修正保留，不重畫素材。

## 已確認缺口

1. `.omx/temari-cyclone-vfx.js` 的颱風分組只找 `age <= sweepDuration`（目前1.2秒）的風流；超過首圈後不再畫風流。`.omx/naruto-temari.js:advanceStorm()` 對接觸目標仍按每目標的 `started` 排程後續切擊，最晚可持續至約2.4秒；因此會出現沒有當段風刃的延遲扣血。圈後被搬動敵人的尾跡不等於後續每刀。
2. `start()` 記住主人起手座標，`emit()` 延後0.18秒／0.4秒仍使用同一座標；身體姿勢則在活主人位置繪製。移動施術時會出現身體和真實風源脫節。此項應由戰鬥作者修釋放採樣，VFX不另造近似來源。

## 最小真實尾段方案

- 首圈保留現有大尺度旋轉前緣，避免用一個持續亮圈假扮多次傷害。
- 戰鬥在每個真正通過生命／範圍／視線／取消檢查的颱風切擊，於既有接觸記錄增加 `lastHit = {x, y, age, angle}`。`x/y` 是當刀接觸快照，`age` 為該storm模擬時間，`angle` 是固定風眼指向該接觸的位置方向。不是命中後持續讀取敵人位置。
- VFX只讀該記錄，在接觸位置畫約0.12秒的短白色斜切和少量青色外緣；首圈後的末刀亦可辨。移動敵人離開後舊刀痕留在命中點，沒有新命中便沒有新刀痕。
- 從現有 `contacts`（及如需物件的 `propContacts`）收集當下有效記錄；同主人同時同地的數量副本可合併表現，維持既有24 field groups和有界接觸標記預算，不能裁減任何真傷害。
- 等待核心作者與主代理確認精確記錄名稱與時間後再實作。繪製不得寫入 `contacts`、刪除記錄、推進時計或更改傷害。

## 驗收閘門

1. 正式入口桌機、390及360手機視窗，正常尺寸看扇、鐮多利、主角及HUD；新尾刀不遮住玩家、敵彈或路面。
2. 控制Lv12／颱風一階／Q0、三個分散有效敵人加範圍外目標，原生影片涵蓋起手、首圈、後續刀、末刀與消散；另有高數量／低畫質片段，不當作自然養成。
3. 每個可見尾刀皆對上當次 `lastHit`；未命中／過期／牆後不畫假命中。離開接觸點的敵人不拖著舊刀痕。
4. 同步繪製前後完整狀態相同；重複繪製不能改變傷害、HP、時計、接觸計數或FX生命。
5. 先檢視本輪實際截圖／影片採樣，使用visual-verdict將具體差異存`.omx/state/temari-complete-20261106/ralph-progress.json`，未通過先回報問題再迭代。分數只評可見性與一致性，不聲稱證明真人樂趣。

## 已落地的產品與自動化

- `.omx/temari-cyclone-vfx.js` 保留原首圈；讀取local `lastHit` 或明示`visualOnly`的ghost `visualHit`，呈現0.12秒固定命中點的短切痕。每field group按空間／當刀時間合併重疊副本，整幀最多48個接觸標記。
- `tools/test_temari_tail_vfx.py` 以正式Canvas入口驗證：舊版首圈後有效命中記錄沒有可見像素（失敗重現）；候選109個可見像素、敵人移動不拖走舊刀痕、過期／無命中／未明示ghost皆不畫、120個重疊副本像素量相同、繪製不改狀態。`--native`另錄三視窗正常入口與受控原生完整相位，不將受控測試標作自然成長。
- `python tools/test_temari_front_selection.py` 通過463個Canvas／選擇案例，pixelEquivalent=true；原普攻／重擊前緣選取契約未改。

## 最終實看與原生證據

`python tools/test_temari_tail_vfx.py --native`通過。實看正常選角及Lv1開局、首圈／中段／尾段／真正末刀／消散後畫面，包含正式遊戲層及同一相位的實際air layer；沒有新角色素材或滿屏遮蔽，扇、主角、敵人及手機控制仍可辨。

- 桌機1200×900：Lv12／颱風一階／精通0／Q0受控靜止elite，三有效及一圈外目標，9次真命中；真正末刀圖在storm age約2.338秒、hit9時擷取。
- 手機390×844：同配置，9次真命中；真正末刀圖在約2.349秒、hit9時擷取。
- 手機360×800低畫質：Lv12／颱風一階／精通0／Q5，三風流、27次真命中；末刀明確等待hit27、約2.333秒，不把較早的hit26標成末刀。
- 三組均有原生RAF影片及末刀後`recovery`圖；階段擷取只暫停現有原生狀態，沒有手推field clock。測試屬明示受控配置，不能代替自然Lv12養成或實機長局。
- 首輪使用boss造成原生光束干擾，已記錄`revise`並改用同樣不被搬動的elite受控靶，重錄後實看通過。這是證據清晰度修正，未為截圖削弱產品敵人。

路徑：本機`.omx/state/temari-tail-vfx/{desktop,mobile390,mobile360-low-q5}/`下的`normal-selection.png`、`normal-lv1.png`、`first/middle/late/last/recovery.png`、`*-air.png`與`native-phases.webm`；時間與命中在`native-report.json`。

錄製來源raw SHA256：核心`c9ce99a94824460fbcc29980249ce9d8da1382d6a7603d8eee66cbc2321c95a6`；VFX`e5b02da7cab5a63ab27600bf6d17f4e4f685732d4b078c73befb59614fa9dfd1`。最終visual-verdict為95／pass，存`.omx/state/temari-complete/ralph-progress.json`，只評上述視覺目標。
