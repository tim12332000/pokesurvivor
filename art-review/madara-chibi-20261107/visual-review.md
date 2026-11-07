# 斑大頭 Q 版：獨立美術複核

日期：2026-11-07。範圍是斑本體的頭身統一；不重新設計技能、須佐與傷害。最終複核為 iteration 2；首次候選保存在 `qa/candidate/`，修正後當前證據在 `qa/candidate-final/`。

## 當次實看與判定

**通過本輪美術範圍，沒有待修的頭身或素材接點阻擋。** 這不是引用舊角色驗收；我實看了當次正常入口、五個動作族全部 48 格的 64px 合成與 socket 覆蓋，以及現行鳴人的同尺寸對照。下列初輪涵蓋仍有效；唯一後續測量修正與最終重驗列於「iteration 2」段。

- 正常入口：`qa/candidate/desktop-normal-entry.png`、`mobile390-normal-entry.png`、`mobile360-normal-entry.png`。本體已有明顯的大頭、短軀幹與短四肢；正常草地場景下沒有再出現舊版細長身體。
- 選角：`desktop-selection.png`、`mobile360-selection.png`。卡片和出戰預覽均顯示同一大頭斑，黑長髮遮單側眼、紅色疊甲及深色衣褲可辨；沒有選角新版、遊戲舊版的分裂。
- `common-64px.png`／`common-64px-sockets.png`：16 格待機、左右踏步、結印、吐火、命令掌、抬臂、受傷、落倒與伏地都已統一比例。倒下維持低平輪廓，沒有為了填滿站高而放大。
- `taijutsu-64px-sockets.png`：10 格的掌、肘、提膝、伸腿、轉踢與落地可分辨；掌點在伸掌端，肘點在前伸肘端，踢擊腳點在伸腿端，沒有標在被大頭遮住的軀幹上。
- `bodyDirections-64px-sockets.png`：8 格正背向體術同樣短身大頭；背向掌／肘與抬腿有各自輪廓，浮空踢與虛擬地面十字保留分離。
- `castingDirections-64px-sockets.png`：6 格正背向結印、吐息與收勢一致；兩個吐息 mouth 點落在當格頭部的可見口側，沒有留在舊版較低的小頭位置。
- `walkDirections-64px.png`：8 格正背向步態全為新版比例，腿部前後交換可辨。另實看 `desktop-body-left.png`，左向鏡射輪廓正常。

## 同尺寸現行角色對照

`qa/candidate/naruto-madara-same-size.png` 使用目前正式 `AnimationAssets.draw` 與 `G.MadaraArt.draw`，兩者同為 **64px 站高**，並列正面、側面與背面。鳴人取現行 `naruto-idle` 正常圖格；不是拿生成大圖或不同縮放圖片作比較。

斑與鳴人均為大頭、緊湊軀幹及短腿，已在同一 Q 版人物比例範圍。斑的黑長髮使頭部外輪廓比鳴人更寬、更低，這是保留原角色輪廓的預期差異；臉與四肢沒有回到先前細長寫實比例。嚴肅表情也保留，沒有為 Q 版改成另一個角色。

## 自動化證據與限制

`python tools/test_madara_chibi.py --label candidate` 通過 1280×900、390×844、360×800，零 pageerror、零 HTTP 缺檔。四向真鍵盤移動以及手機觸控移動通過。`qa/candidate/report.json` 的正常 Animator drawImage 來源確認左右使用 `madara-actions-chibi-v1-runtime.png`，上下使用 `madara-walk-directions-chibi-v1-runtime.png`；五張圖集 SHA256 與最後落地的 `frames.json` 相同。

48 格合成與 socket 覆蓋是當前素材登記的檢視證據，不能單獨證明每個攻擊相位的完整播放或傷害碰撞。完整戰鬥幾何與生命週期交由既有角色回歸測試另驗；本輪不宣稱重跑自然養成、實機長局、音效聽評或真人樂趣。無新增依賴，未更動他人素材與技能。

## Iteration 2：真掌面接觸點修正後重驗

原有完整戰鬥回歸指出首次分身掌擊邊界未觸及；進一步源圖測量確認 `taijutsu` 第 1 格掌點原在手套內側 `(690,224)`。素材代理將它移到同格不透明前緣 `(706,224)`，該像素 alpha 為 253；runtime socket 由 `[99.141,62.133]` 改為 `[104.573,62.133]`。這是素材接觸位置校準，沒有改攻擊程式、數值或圖像。

我在最終 metadata 凍結後重新執行 `python tools/test_madara_chibi.py --label candidate-final`：桌機、390／360 手機正常入口、鍵盤／觸控與五圖集合成都通過，零錯誤／缺檔。已重新實看 `qa/candidate-final/taijutsu-64px-sockets.png`，掌點位於伸掌的外側接觸面；並核對 `palm-source-leading-edge.png` 的 6 倍源圖局部，青圈新點在手套最前緣，紫圈舊點確實在手套內。此局部圖僅作測量診斷，未覆寫任何素材。

另重看最終同站高 `naruto-madara-same-size.png` 與 `mobile390-normal-entry.png`，頭身與正常入口結論相同。五張 runtime PNG 的 SHA256 全與首輪相同，最終 capture report 的掌點亦與當前 `frames.json` 相符。最終視覺放行以 `qa/candidate-final/report.json` 與 iteration 2 結構化判定為準；首輪的靜態目測未能辨出這個內側掌點，不能取代本次源圖與戰鬥回歸的校準。

結構化判定存於 `.omx/state/madara-chibi/ralph-progress.json`。分數只作流程訊號；本次通過依據為上述實際比例、48 格涵蓋、嘴手腳登記、正常入口與正式來源核對。
