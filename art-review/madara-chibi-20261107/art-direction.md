# 斑的大頭 Q 版比例修正

使用者授權：斑全部人物動作改為與其他角色一致的大頭 Q 版，完成後發布。

範圍是 common 16、taijutsu 10、bodyDirections 8、castingDirections 6、walkDirections 8，共 48 格本體；木分身共享本體。保留穢土斑黑長髮、遮眼、紅疊甲、深衣、護脛和涼鞋。須佐、火、隕石及木材質不改造型，玩法／傷害／成長不變。

原問題：當前斑素材本身是小頭長身，runtime 等比例縮放無法修正頭身。以現用 `art-review/redrawn/naruto-common-v1.png` 作比例與描邊參照，以五組現用斑圖集作逐格動作參照。新素材使用內建 imagegen 編輯，保存原始輸出副本，不用程式拉伸身體或貼大頭。

驗收：同一 64px 正常身高下檢查所有本體格、前後及鏡射；以族群站高規格化，倒地、蹲身不逐格放大；依新圖重測嘴／掌／肘／足與腳底。正式選角與 Lv1 開局、鍵盤／觸控、桌機／360／390；既有命中和生命週期回歸，公開新圖雜湊與正常入口核對。靜態圖集與受控招式畫面不冒充自然養成或玩家主觀樂趣。

產物與驗收細節：`generation-records.json`、`qa/`、`release.md`。新版可重建工具 `tools/build_madara_chibi_assets.py`，正常載入仍沿用 `art-review/madara/runtime.js` 與 `frames.json`。
