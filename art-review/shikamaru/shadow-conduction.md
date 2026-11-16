# 大捕縛：沿影線導電

依使用者最新指定，保留自身範圍、每敵直尖影、過身後拘束，以及最後的炸彈；在兩者之間新增 **三道沿線傳送、抵達才電擊的脈衝**。「影線導電」為本作改編，不聲稱鹿丸原作會雷切。

## 玩家看到與真正發生的事

1. 抬手蓄勢、低身、結印，直尖影逐人穿身，完成後約0.12秒收成細黑連線；每條有效連線都保留，不再讓粗箭頭全程撐成海膽。
2. 初始捕縛完成或失效後，先留0.12秒，再沿每條有效影線送出三道藍白電流，間隔0.18秒。電流有可見前沿與傳送時間，沒有瞬間整線常亮；最短飛行0.24秒。
3. 每個封包真正抵達目標身體才造成 electric 傷害與短電弧反應，命中點保存當次世界位置。中途斷線、死亡、退學、換場或清場會取消未來電擊；不由繪製扣血。
4. 初始目標的三個封包都完成或失效後，才投一顆帶符炸彈。保留短投擲前搖、釋放與收勢；中段側拋露回本體，源點、落點與時計不被繪製拖動。最後是暖橙不規則火舌、破碎衝擊弧與碎煙，移除原本等角橢圓花圈。

基礎CD仍32秒、圓半徑仍260、目標數仍無上限，數量卡仍只擴範圍。原本總基礎傷害45拆成電擊每輪15%×3＋炸彈55%，合計100%；屬性、天氣及原生每筆取整另計。技能升階／卡牌預覽從同一 profile 讀取每輪電傷、輪次與爆傷。舊詰將及其他角色未重做；沒有新增依賴或點陣素材。

## 修改檔案與重用

- `.omx/naruto-shikamaru-mass.js`：封包排程、抵達真傷、先電後投彈、只讀電流／收細查詢、局部特效及本招姿勢。
- `art-review/shikamaru-art.js`、`art-review/shikamaru/reference-shadow-geometry.js`：本招專屬結印／投擲／收勢；移動仍跑步，人物與地影朝向一致，受傷／倒下優先。重用既有圖格與共同時計。
- `.omx/naruto-skills.js`、`.omx/jujutsu-growth.js`、`.omx/digimon.html`：說明、真收益預覽及資產版本。
- `tools/test_shikamaru_mass_conduction.py`：新增抵達、順序、連線、取消、分身與演出查詢測試；既有mass、姿勢、原生與自然驗證同步更新。

## 當次證據

- [導電機制](qa/mass/conduction/mechanics.json)：前沿progress約0.0686時零傷；抵達後每敵三次電擊＋一次炸彈。同場300敵含4首領＝900次電擊＋300次爆破，沒有目標數上限。移動來源、沿線共線、凍結命中點、牆阻／生命周期、shock與bomb的hurt／onDealt同波取消、分身隔離及render/query只讀通過。
- [一般回歸](qa/mass/mechanics.json)：低總傷、32秒、先穿身拘束、三包抵達後投彈、後進圈、首領、極淺柔邊提示及成長均通過。控制捕縛本身不扣血。
- [原生桌機／360／390](qa/mass/conduction/native/report.json)：18原生百萬HP靶、實際Lv6學卡，原生RAF播放準備／刺入／拘束／電流在途／抵達／投彈／爆破／消散。受控配置不當自然養成；美術／姿勢分別實看當輪畫面，側拋修正另重錄。
- [自然局](qa/mass/conduction/natural/report.json)：全新Lv1正常開局、不改HP／XP／敵AI／clock，54.36秒Lv6真選卡，主玩家第一發有4次電擊與2次爆傷，完整同一發解除後63.71秒仍滿血235。此機制錄影後只再改了不影響命中／時計的投彈中段側偏。
- 現行九個標準Node檢查、姿勢／投影效能、修改JS語法與 `git diff --check` 通過。後續發布從乾淨來源建置，沿用當前Pages設定，並核對公開檔案與桌機／手機真入口。

仍有限制：多目標電流在近源端短暫交疊；已看畫面中鹿丸頭部、敵方血條與HUD可辨。未驗手機實機長局、音效聽評及合作guest同步；視覺放行不代替使用者對帥氣與樂趣的判斷。

## 發布完成

[正式遊玩導電版鹿丸](https://tim12332000.github.io/pokesurvivor/?lang=zh-TW&hero=shikamaru&release=1a94af11)

遊戲來源 `1a94af1119e46fbf40ceb7cf73d7b73abddb13f1`，靜態提交 `66ab28b54bbbd97c5e797b0a9b8028852de341d9`，Pages來源 `codex/shikamaru-conduction-pages-1a94af11:/`。沿當時真實線上靜態 `ddae37a34a8781885e451aac8ff08aae74ba6dec` 更新，保留13,855個既有公開檔案；僅六個runtime／入口及新manifest改變。網址、HTTPS、CNAME、default main與保護維持原設定。

公開 [manifest](https://tim12332000.github.io/pokesurvivor/shikamaru-conduction-release.json) 與20個核對檔案符合canonical artifact及靜態Git blob。正式根入口的桌機及390手機、冷／暖快取，皆真正從Lv1開局、自然命中及真按鍵移動；公開程式另通過影線移動、300敵、三個真電流抵達後傷害／完電才丟彈、所有清理與回呼取消測試，零pageerror／缺失請求。沒有攔截或替換公開程式，不把push或queued當發布完成。

發布證據位於 `.omx/state/shikamaru-conduction-release/` 的 `release.json`、`static-artifact.json`、`public-assets.json`、`public-browser.json`、`remote-after.json`。無關三份原有QA髒檔保留，未提交或打包。
