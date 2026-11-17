# 分支整併完成記錄

2026-11-17完成使用者確認的獨立修改版整理。

## 結果

- 遠端從28條舊分支收斂成 **`mod-main`**、**`gh-pages`** 兩條。
- 本倉庫預設分支與目前工作分支均為 `mod-main`；`origin/HEAD` 已對應。原作 `upstream/main`、`upstream/live` 及remote設定保留，沒有合併上游。
- 32個舊head先推送並逐SHA驗證成 `archive/2026-11-17/*` tags，再以expected-head lease刪除舊branch refs。
- `gh-pages` 直接指向原線上靜態commit `6df23b58042a914cd4363b216aba87f38dcc3dc5`，沒有修改遊戲tree。另有回溯tag `releases/20261117-migration-f6d40787`。
- Pages仍是 `legacy`、來源 `gh-pages:/`；[遊戲原網址](https://tim12332000.github.io/pokesurvivor/) 、HTTPS及CNAME設定不變。
- 保留既有 `github-pages` environment與保護規則，只把原本允許舊主線的同一項branch policy從 `feat/digimon-sandbox` 對應到 `mod-main`，未降低審批或限制。

## 驗證與簡化

- 原28個公開資產hash完全相同；原角色分享網址可正常Lv1開局，桌機／390手機冷暖快取與實際自動穿刺、54次導電、18次爆傷完整通過。一次原生PNG暫時503另重抓為200且bytes相同，紀錄沒有當作缺檔掩蓋。
- 固定分支工具的10個臨時Git整合測試通過，含dry-run不改refs/index、歷史資產／LICENSE EOL保留、private/raw排除、lease及push advertisement後source前進的真競態。
- 真實Windows乾淨checkout及實際建置包完成dry-run：refs與原index完全未變，僅預告新增 `release.json`，動態核對183個入口／runtime檔案。真實source為 `04a4d594b85793ccdb98c202151d94280aa68a4e`，遊戲檔案與遷移前相同。
- 現行九個標準Node檢查、Python編譯及diff檢查通過。
- 修改檔案為 `.github/workflows/digimon-pages.yml`、`AGENTS.md`、`tools/publish_mod_pages.py`、`tools/test_publish_mod_pages.py` 及本次三份分支文件。以單一工具／固定分支取代每角色新建Pages分支，保留現有遊戲與依賴。

使用方式與限制見 [分支管理及發布流程](branch-management.md)。工具不把source no-op誤稱原子鎖；push後及要求build前會重新比對source，偵測前進時要求抓取／重建，不回滾並行工作。

## 保留資料與外部限制

42個舊工作樹都有tracked修改、untracked或ignored內容之一，因此沒有刪除任何工作樹目錄。本地只額外保留三個被有資料工作樹使用的舊分支：鹿丸重設、Ryu、英文版。三份根工作區原有QA髒檔亦以SHA核對未改，未帶入提交。

GitHub目前仍對workflow dispatch回HTTP422「Actions has been disabled for this repository」。固定workflow已更新並保留環境gate，但沒有更動Actions啟用設定或保護來繞過；雲端執行不能宣稱通過。本機固定分支工具已實測可準備發布，現有公開站不受影響。

完整快照、archive mapping、工作樹盤點、ref清理結果、環境前後比對、公開核對及真實dry-run存於 `.omx/state/branch-consolidation/`。
