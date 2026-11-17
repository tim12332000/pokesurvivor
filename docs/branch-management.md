# 修改版主線與發布方式

本倉庫是獨立修改版，原作維持 `upstream/main` 參照。正式來源已整合到 **`mod-main`**，也是本倉庫預設分支；公開靜態成品固定使用 **`gh-pages:/`**。

遊戲網址保持 [https://tim12332000.github.io/pokesurvivor/](https://tim12332000.github.io/pokesurvivor/)。整理分支不改倉庫名稱、網域、HTTPS、角色網址或既有遊戲bytes；先前帶 `hero`／`release` 參數的分享連結仍開啟目前線上版本。

## 開發

以 `mod-main` 為整合來源。需要隔離開發時可用短期 `codex/*` 功能分支，完成後整合並清理；不要再為每個角色建立長期Pages分支。不要把靜態成品merge回原始碼，也不要為整理本倉庫而合併原作上游。

根工作區現有未提交QA及其他研究產物保留原樣。發布時使用已提交並推送的來源，以及乾淨checkout；工具會拒絕tracked檔案尚未提交的來源。

## 固定發布

現有 `.github/workflows/digimon-pages.yml` 監看 `mod-main`，執行既有九個標準Node檢查及發布工具的Git整合測試，再建置並更新固定 `gh-pages`。它會明確要求目前legacy Pages建置，不修改Pages設定或服務保護。

本機可從乾淨的、已推送的 `mod-main` checkout使用相同流程：

```powershell
git fetch origin
python tools/build_digimon_site.py
python tools/publish_mod_pages.py --dry-run
python tools/publish_mod_pages.py --push
```

`--dry-run` 不建立branch/tag refs，也不修改來源、原index或原artifact；預設不加參數只準備本地發布，只有 `--push` 才推到遠端。若雲端Actions不可用，本機流程仍可用；需以現有憑證對既有legacy站要求build並核對公開內容，不更動保護。

發布工具固定保留舊靜態資產與EOL等價bytes，對照來源、重算入口內容hash及LF2／Madara的metadata快取參數；原index用獨立暫存index隔離。先檢查來源／發布head，push用預期head及fast-forward保護，並於push後再次檢查來源。若開發主線在發布中前進，需從最新來源重新建置，不可把過時建置回報為最新。

GitHub Actions使用的 `GITHUB_TOKEN` 推送不會自行啟動Pages建置，因此workflow另有guard及明確build request；這是[GitHub官方限制](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)，不是要求修改保護。

## 歷史與工作樹

2026-11-17的32個舊分支head已保存成遠端tag：`archive/2026-11-17/*`。例如舊整合版是 `archive/2026-11-17/feat/digimon-sandbox`，舊正式靜態版是 `archive/2026-11-17/codex/shikamaru-entry-pages-f6d40787`。後續正式發布用 `releases/*` tag保存靜態commit及其來源manifest。

遠端僅保留兩條正式分支。本地三個舊分支仍被有資料的工作樹使用，因此保留：`codex/shikamaru-reference-redesign`、`feat/ryu-sky-scatter-20261106`、`release/naruto-english`。42個工作樹都有未提交／未追蹤／ignored內容之一，沒有刪除任何目錄；需要清磁碟時再逐份確認用途，不能把研究、QA或錄影視作可丟棄產物。

整併前後快照與完整工作樹盤點在 `.omx/state/branch-consolidation/`。目前根工作區三份原有QA檔的bytes已另做前後核對。
