# 表蓮華重新設計

本機互動預覽：<http://127.0.0.1:8004/art-review/lee-front-preview/>。
預設靜音，提供慢放、重播、技能階級與八門形態。使用正常遊戲的角色、戰鬥與動畫程式。

## 影片觀察與改編

- [原作準備／踢起片段](https://tenor.com/view/rock-lee-primary-lotus-naruto-gaara-chunin-exams-gif-26437906)：解開繃帶、踢起目標，再追至背後。已在本機拆幀確認。
- [表蓮華抱持／倒栽旋落片段](https://tenor.com/view/rock-lee-front-lotus-gif-23305135)：此為雪地場景的版本；後段可見抱緊、繃帶纏繞、兩人翻至頭朝下並旋轉落地。已在本機拆幀確認，不將此片段誤標為中忍考試全片。
- [官方第49集介紹](https://naruto-official.com/en/anime/naruto1/list/01_273) 作為少年小李招式的角色依據；[Ninja Council 3](https://spritedatabase.net/game/55) 為既有風格研究入口。
- 時間、傷害比例與周圍落地震擊沿用／調整為俯視生存遊戲演出，不宣稱逐鏡重製原動畫。

## 實作

新增 `redrawn/lee-front-lotus-hold-v1.png`，由 imagegen 參考既有小李與八門圖集生成，沒有挪用原片圖像。正常／八門各四格：伸手、抱持、專門倒立姿勢、放手。使用新抱持圖，沒有以站姿旋轉冒充抱摔。

角色手部依每格 `grip` 錨點對齊任意敵人的腰部，敵人繞腰部翻至頭朝下，下降時維持抱持與旋轉繃帶。保留原生 `jumpLift`，首領不強制浮空。固定鏡頭至收招、取消震屏；弱目標延至落地才擊倒。

挑空基準高度由84提高至240；依固定視野保留頭部空間，普通手機視野可呈現完整高度。預覽增加垂直空間，讓高點抱持與墜落落差清楚可見。

表蓮華數值維持原值：CD5秒，傷害110／132／132／132／165，主目標20%挑空＋80%落地；次要目標只吃一次35%落地震擊，基礎拉三名、最多十二名。演出約1.97秒另加起手。

## 驗證

- `python tools/test_lee_front_redesign.py`：桌機／手機、正常／八門、首領、弱目標與取消；專用圖集、抱持到倒立姿勢、兩段傷害、三名範圍內敵人與範圍外排除、無空中無敵與固定鏡頭。
- `python tools/capture_lee_front_preview.py`：真正遊戲繪製的六階段分鏡與GIF，含抱持、倒立、下降前中後的近照；手機高階八門與預設靜音／音效開關。
- 證據：`.omx/state/lee-front-lotus/`，主要動圖 `front-lotus-redesign.gif`，分鏡 `front-lotus-storyboard.png`。
- `python tools/test_lee_reverse_balance.py` 與 `python tools/test_lee_reverse_presentation.py`：另驗證使用者指定的裏蓮華傷害、CD與拉取人數翻倍，以及群踢／鏡頭回歸。
- 舊固定數量／單體蓮華測試保留歷史假設；本次不宣稱整套歷史測試全數通過。
