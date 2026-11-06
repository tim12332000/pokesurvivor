# 重製版發布記錄

已於原網址完成發布：[遊玩斑](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=madara&release=c54dc3cc)／[自然成長及桌機手機實錄](https://tim12332000.github.io/pokesurvivor/assets/previews/madara-rework.html)。

| 項目 | 實際值 |
| --- | --- |
| 遊戲來源提交 | `c54dc3cc165723cb54a9705ec5aade36753c0836` |
| 靜態發布提交 | `117ac8e7502bc77c348abf13efe20389b2f06d33` |
| Pages來源 | `codex/madara-pages-c54dc3cc`，路徑`/`，模式`legacy` |
| 網址與HTTPS | 沿用原GitHub Pages網址及HTTPS；CNAME仍為null |

## 發布流程

來源推送成功但沒有產生Actions run或check；直接dispatch回覆HTTP422「Actions has been disabled for this repository」。倉庫政策實際為enabled=true、allowed_actions=all，workflow也為active。重新確認啟用後仍遭相同拒絕，最後政策維持原值。本次沒有宣稱hosted Actions通過。

改以獨立canonical Git worktree建置同一來源提交，核對重要文字bytes等於Git blob，執行九個標準Node檢查及原有正式產生器。經獨立暫存index建立只含靜態包的發布提交；沒有改寫來源歷史或更改default main。

依[GitHub Pages設定API](https://docs.github.com/en/rest/pages/pages#update-information-about-a-github-pages-site)改用上述分支來源。API接受201 queued，但build-history未提供可用紀錄，因此最終以公開內容及真瀏覽器結果判斷，而非把queued當成功。

## 已完成的公開核對

- 入口、核心程式、metadata、14張runtime PNG及實錄頁共25個關鍵檔，公開bytes與發布提交完全相同；PNG另符合metadata SHA。
- 全新桌機及360手機視窗正常從Lv1開局，version2、14張素材、上下專姿與新文案均實際載入，零頁面錯誤／缺失請求；正常開局沒有請求展示影片。
- 四份公開影片均可真正seek至3秒並播放，HTTP Range回206，Content-Range及前128bytes一致，媒體類型正確。
- CRLF／LF差異以[來源雜湊](rework-source-hashes.json)分開記錄；部署比較對象為Git blob與實際公開bytes，沒有混稱Windows工作樹raw SHA。

完整公開核對資料另保留本機`.omx/state/madara-rework/public-v2-assets.json`及`public-v2-browser.json`。

## 後續更新

目前feature branch的push不會自動更新這個分支來源。Actions仍不可執行時，應從新來源提交建置並核對canonical靜態包，再更新可追溯的發布分支／Pages來源；保留`.nojekyll`，不帶上游CNAME，不加入本機快照或原始錄影。

若Actions恢復，先確認真dispatch可執行，再按既有workflow恢復`build_type=workflow`。不要僅憑政策enabled宣稱已恢復。本次沒有安排背景切換，遊戲程式及存檔ID不因發布方式而改動。
