# 斑頭身統一：當次驗證

`tools/test_madara_chibi.py` 從目前工作樹的正常選角／開始入口載入。預設自行使用隨機本機埠，避免測到其他工作樹。

```powershell
python tools/test_madara_chibi.py --label baseline
python tools/test_madara_chibi.py --label candidate
```

也可用 `--url <正式打包入口>` 核對同一渲染路徑的發布候選。`report.json` 記錄當次五張本體圖集來源與 SHA256。

## 證據範圍

- `desktop` 1280×900、`mobile390` 390×844、`mobile360` 360×800：正常選角及開局截圖，真鍵盤四向輸入，手機另驗真觸控移動。
- `*-body-{direction}.png`：正常人物 Animator 的當次 drawImage 來源與渲染結果；細節記在 `report.json`。
- 五張 `*-64px.png`：當前已載入 runtime 圖集，依當格裁切／腳底錨點以 64px 站高合成；蹲姿與倒下不放大。這是素材渲染探針，不是遊戲中的動作時序證據。
- `naruto-madara-same-size.png`：當前鳴人與斑的正式素材繪製函式並列正／側／背面，均為 64px 站高，沒有輸出後另外縮放。鳴人取現行 `naruto-idle` 的正常待機圖格。
- `*-64px-sockets.png`：同一素材加錨點。白十字是腳底錨點；黃點 mouth、青點 palm、紫點 elbow、紅點 foot。僅表示當格登記，仍需人工核對嘴、手、肘、腳的實際位置。
- 此工具不宣稱自然養成、完整大招、高配長局效能或真人樂趣通過。戰鬥幾何與生命週期使用既有 `tools/test_madara_rework.py` 另驗。

## Baseline（修改前）

2026-11-07 當次正常入口與輸入三種尺寸均通過，零 pageerror／HTTP缺檔。實看 `baseline/common-64px.png`、`baseline/mobile390-normal-entry.png`、`baseline/taijutsu-64px-sockets.png`、`baseline/castingDirections-64px-sockets.png`：本體呈細長四肢及小臉輪廓，確實與大頭 Q 版的目標不符。此結論不沿用先前角色驗收的分數。
