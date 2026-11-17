# 修改版分支整併計畫

使用者已確認：修改版使用 `mod-main` 作正式主線、固定 `gh-pages` 發布，原作 `upstream/main` 保持獨立；原有遊戲網址與角色分享連結繼續有效。

## 執行與驗證

1. 保存目前本地／遠端分支、預設分支、Pages來源與工作樹狀態。保留現有三份未提交QA檔及所有使用者／研究產物。
2. 為舊遠端與本地分支建立可回溯的archive tags，先驗證遠端tags確實指向原SHA，再整理branch refs。
3. 將現有整合來源轉為 `mod-main`，推送並設為本倉庫預設分支；保留原作remote和其main，不合併上游歷史。
4. 從目前已驗證的公開靜態head建立 `gh-pages`，直接保留相同tree與bytes，切換Pages來源後核對網址／HTTPS／網域與公開資產、自動施放不變。
5. 更新固定分支發布工具、workflow和專案指引。發布工具需有dry-run／整合驗證，使用fast-forward及expected-head保護，後續以release tags回溯，不再為角色新增Pages分支。
6. 只整理已被主線包含的舊來源分支和已封存的發布分支。工作樹只移除倉庫內、完全乾淨且沒有untracked／ignored內容的舊detached checkout；其他工作樹保留，必要時只解除舊分支綁定。

## 保留與回復

- 不把靜態成品merge進來源，不改遊戲程式或數值。
- 不改倉庫名稱、Pages網址、CNAME、HTTPS或服務保護。
- 所有ref整理先驗原SHA；遇到並行更新就保留並重新檢查，避免覆蓋新工作。
- archive tags保存舊head；目前公開head另外設發布tag，必要時可把Pages切回同一靜態提交。
