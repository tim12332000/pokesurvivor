# 火影動作演出審閱室

這是獨立分支 `feat/animation-presentation-lab` 的美術研究與提案資料夾。候選作品先由製作端檢查，最後交由使用者審核；**使用者明確同意之前，不合併回遊戲分支，不接入正式遊戲。**

本地審閱網址：<http://127.0.0.1:8317/art-review/index.html>。使用獨立埠與獨立輸出目錄；直接用 `file://` 開啟無法讀取候選清單。

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
    "summary": "這版要解決的視覺問題。",
    "improvements": ["具體改善"],
    "limitations": ["尚未完成的部分"],
    "references": [{"title": "參考來源", "url": "https://example.com/"}],
    "qa": {"score": 90, "verdict": "製作端的實際檢查結論"}
  }]
}
```

`beforeImage` 可省略；`kind` 使用「AI概念稿」或「原圖動作預覽」。來源請記錄能直接支持該動作或造型的頁面，勿把遊戲改編效果誤稱為原作設定。新增素材後也須檢查版權、透明背景、角色比例、動作方向與現有素材的風格一致性。
