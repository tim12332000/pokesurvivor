# 火影動作演出審閱室

目前版本：鳴人、佐助、小李及一尾、八門形態使用九張重新繪製的圖集，共 216 個實體影格。Ninja Council 3 僅作比例、描邊和動作語意參考，現用角色圖沒有直接複製該遊戲素材。生成方式、完整提示詞及檔案雜湊見 [redrawn/provenance.json](redrawn/provenance.json)。

這是鳴人、佐助與小李的美術研究與審稿資料夾。重繪已合併至 `feat/digimon-sandbox`，小李依新增角色指示接入正常選角與遊戲。

本地審閱網址：<http://127.0.0.1:8004/art-review/index.html>。使用獨立埠與獨立輸出目錄；直接用 `file://` 開啟無法讀取候選清單。

完整動作內測：<http://127.0.0.1:8004/art-review/playtest.html>。從本 worktree 執行 `python tools/serve_animation_lab.py --port 8004`；這個網址讀取完整遊戲與審稿試驗，獨立匯出的 8317 服務則只供看圖。專用本機服務使用較大的連線佇列，避免大量精靈圖同時載入時被拒絕。「新版完整動作」預設開啟，涵蓋三位角色與分身；取消勾選可對照原版。遊戲內與上方都有升級按鈕，可解鎖所有招式並用選單逐招測試。實際素材與姿勢組合的範圍見 [gameplay-contract.md](gameplay-contract.md)。

原有鳴人／佐助 17 組演出及小李普通、八門形態共十八組動作皆接入目前自繪圖集。八門於 Lv.6 起學會後永久被動生效，不佔主動槽；五階使用專用紅臉、白眼與豎髮動作，第三階起加強氣場。小李招式與驗證見 [lee-skill-design.md](lee-skill-design.md)。審稿頁顯示九張現用圖集；前版十一項提案清單保留於 `redrawn/legacy-manifest.json` 作歷史對照。

執行 `python tools/build_animation_review.py` 只會輸出審稿頁至本 worktree 的 `dist-animation-review/`，不執行遊戲打包或發布。從該目錄執行 `python -m http.server 8317 --bind 127.0.0.1` 即可開啟。現有遊戲的 8002 埠、原分支與 GitHub Pages 保持獨立；此分支推送不符合原發布工作流程的分支觸發條件。

## 資料夾

```text
art-review/
  index.html          圖片審閱頁
  gallery.js          候選清單、篩選、本地審閱紀錄、JSON 匯出
  style.css           審閱介面樣式
  manifest.json       候選作品與初審結果
  research.md         動作研究及來源說明
  candidates/         通過製作端初審的候選圖
  references/         原素材或資料來源的參考圖
  previews/           動作比較或預覽輸出
```

## 審閱

點圖片可另開原尺寸檔案。每件作品可選「認可這版」、「需要修改」、「不採用」，並填寫備註。紀錄儲存在目前網址的瀏覽器 localStorage；不同瀏覽器、連接埠或電腦不會自動同步。請使用「匯出審閱紀錄 JSON」保留決定與修改方向。

「認可」是審閱紀錄，不是自動合併命令。AI 概念稿亦不代表已有完整逐幀動畫或可直接使用的透明 sprite sheet。

## 增加候選作品

先將圖片放入 `candidates/`，再在 `manifest.json` 的 `items` 增加一筆。只有 `status: "candidate"` 且有合法本地圖片路徑的項目會顯示；不要為尚未產生的圖建立空卡片。保留穩定且唯一的 `id`，讓審閱紀錄能對應作品。初審淘汰的項目改成其他狀態即可隱藏。

```json
{
  "branch": "feat/animation-presentation-lab",
  "baseCommit": "起始 commit",
  "items": [{
    "id": "sasuke-chidori-01",
    "title": "千鳥蓄力演出提案",
    "character": "佐助",
    "status": "candidate",
    "image": "candidates/sasuke-chidori-01.png",
    "beforeImage": "references/sasuke-current.png",
    "kind": "AI概念稿",
    "category": "skill",
    "animation": {"columns": 4, "rows": 2, "fps": 7, "sequences": [{"name": "施術", "frames": [0, 1, 2, 3, 4, 5, 6, 7]}]},
    "summary": "這版要解決的視覺問題。",
    "improvements": ["具體改善"],
    "limitations": ["尚未完成的部分"],
    "references": [{"title": "參考來源", "url": "https://example.com/"}],
    "qa": {"score": 90, "verdict": "製作端的實際檢查結論"}
  }]
}
```

`beforeImage` 可省略；`kind` 使用「AI概念稿」或「原圖動作預覽」。來源請記錄能直接支持該動作或造型的頁面，勿把遊戲改編效果誤稱為原作設定。新增素材後也須檢查版權、透明背景、角色比例、動作方向與現有素材的風格一致性。

`category` 使用 `movement`（方向移動）、`common`（共通動作）或 `skill`（技能演出），可與角色交叉篩選。`animation` 可省略，省略時顯示靜態圖。格線由左至右、由上至下編號，第一格為 `0`；例如 4 欄 × 4 列的四方向圖，每一列可分別設定 `[0,1,2,3]`、`[4,5,6,7]`、`[8,9,10,11]`、`[12,13,14,15]`。

看圖頁的播放器可切換方向／動作、暫停、逐格查看及調整 FPS。完整圖集收在播放器下方的「查看完整圖集」。只有畫面內可見的播放器會推進影格，切換篩選後會停止舊播放器。看圖頁仍使用未對齊遊戲錨點的格線預覽；完整動作內測另用逐格人物裁切與腳底座標，實際接線範圍見 [gameplay-contract.md](gameplay-contract.md)。
