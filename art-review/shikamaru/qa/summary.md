# 鹿丸 QA 交付紀錄

2026-11-16。本檔區分原生自然觀察、受控驗收與視覺定點證據，不把測試全綠稱作真人好玩。

## 最新受控驗收

`tools/test_shikamaru.py` 六組通過；`controlled/report.json` 保存完整來源 SHA256 與前後穩定性（true）。

- progression：正常選角 Lv1 僅影真似；Lv2/3/4/5 真卡門檻；五招合法學習；技能池不污染小李；戰術真升階增加分枝1、束縛0.12秒且傷害維持0。
- geometry：影真似、影縫、陷阱三個有效目標＋範圍外；傷害經原生hurt且歸屬正確；施放後牆阻擋接觸。
- lifecycle：pause/clear/death/world取消；首靶hurt回呼取消後，同波第二靶和未來接觸均不補打。
- growth：真正第一張數量卡應用，分散目標／實際命中消費端增加，非只比較profile數字。
- control：普通／強敵 × 本體／真正SelfClones，未束縛接觸扣血、普通held不扣血、強敵仍能攻擊、解除後接觸恢復；bound期間burn/poison/slow原生時計和DOT持續，位置固定。在途原生敵彈不被移除且仍可擊傷玩家。
- strangle：先由影真似實際捕捉再首縛，首段／後段真接觸成立；旁邊未綁目標不受首縛傷；取消後不補未來段。

## 自然 Lv1 成形

`natural-frozen/attempt-1/run.json`、`native-play.webm`、選卡PNG和`natural-frozen/report.json`：正常入口、零永久升級，真鍵盤走位、自然敵潮、真UI選卡，沒有改XP/HP/敵潮/技能clock或推sim。

同一局觀察285.320秒，Lv23、22張卡，五招自然學成。終局影真似5、影縫3、陷阱5、戰術3、首縛2；真正傷害事件分別1194、970、180、204次（戰術無假輸出）。此局最後死亡；保留完整終局，不宣稱存活300秒。零pageerror。來源在該次遊玩前後穩定。

這之後只修正美術方向分派和首縛手依敵人bodyH錨點／縮放，無傷害、時計或成長變更。自然片不冒稱包含較新的美術修正。最新畫面以以下定點片證明。

較早的`natural/attempt-1`及`attempt-2`是製作中探索（sourceStable=false），保留死亡反例，不作最終版本來源證明。

## 最新原生視覺證據

- `native-final-cardinal/`：影真似、影縫、首縛及四向陷阱的原生RAF連續演示；受控rank3、Q2、百萬血靜靶，非自然成長。含原生HUD、當段state與來源manifest。
- `trap-phases-release/`：最終四向各prepare/release/recover共12張原生canvas影格、連續影片、pose age/frame key與manifest。正常render呼叫後取樣，不推clock、不暫停截相位。sourceStable=true，零pageerror。
- `strangle-body-final/`：最新首縛小型敵人bodyH39；真pulse1/3/5首／中／末影格及完整連續片，age .272/.720/1.184。sourceStable=true，零pageerror。

美術與動漫已收到上述最新產物，須由各自獨立驗收，QA不代替其放行。未做手機真機長局或音效聽評。

- strangle-settled/：依動漫檢視反例補一張原生effect.age .14–.18的非首擊影格，避免hurt白閃遮住沿身手型；只增觀察捕獲。附同局原生片、完整manifest，sourceStable=true，零pageerror。
