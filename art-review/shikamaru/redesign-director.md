# 鹿丸重設計：獨立總監看板

## 真runtime製作看板（本隔離樹最新狀態）

工作樹：`C:/Git/pokesurvivor/.omx/worktrees/shikamaru-reference-redesign`，base `a67cbcd4`；正常驗證port8351。只保護本任務範圍，root舊renderer／材質WIP不套回、不發布，外部Naruto改動保留。總監只寫本文件，不改產品、不另派agent。

**當前：真產品候選已獨立放行，待root公開核對。** 依據是新runtime真幾何、安全、自然成形與當輪產品原生畫面；下方研究／prototype歷史已被本節真產品結果取代，不用prototype通過冒充角色完成。

| lane／關卡 | 已落實物 | 尚缺依賴／下一個可驗成果 |
| --- | --- | --- |
| 戰鬥／renderer | 新v6真alpha接影、原地束縛、融合及xyz下降掃掠；幾何與原生畫面核證 | 無候選阻擋 |
| 企劃接點 | 保留30017／真卡管線；首縛退出新池，說明與預覽對真消費端 | 無候選阻擋 |
| 身體／美術 | 新產品桌機／390四向與自然已各自實看；兩片真播至末10.56／9.52秒 | 無候選阻擋，非prototype代驗 |
| QA | alpha/cache/arch＋6組core安全全過；75.44秒Lv7／6真卡／20影縫hurt自然完整循環 | sourceStable／零error，無候選阻擋 |
| 總監／動漫 | 各自核新源碼／實物；已退回問題修後獨立重驗 | 真產品候選放行；root負責正式包／公開bytes／真正開局核對 |

首要判準：不以舊圓池／粗管／敵腳冰刺換皮；敵人必用自己的alpha，不把怪都畫鹿丸影。群片只融合已捕投影、不用凸包偷AOE；影縫從同一地影鼓起再升拱，前後端點真掃掠接身，不用展示時間扣血。繪製只讀模擬，276原地束縛不引回同步拖敵。

### 真產品候選結論

美術已明確完成新8351正常／自然及四向實物審查，另親看390右下降前、左xyz真傷、下收勢；桌機／390兩片真播放至末，SHA及ended記錄在 `qa/reference-redesign/art-runtime-review/four-direction-playback.json`。與總監／動漫新產品獨立結論相符，全部候選阻擋清零。可提交部署，不再新增研究、首縛、原型或無關長局。

公開版本仍待root核對，本看板不宣稱已上線；亦不宣稱使用者已認可好看／好玩。保留非手機實機長局、音效未聽評的界線。以下退回與prototype文字為歷史，最新真產品放行以本節為準。

### 首段新runtime實物與退回

已讀新 `reference-shadow-geometry.js` 與module diff：當格owner／原生enemy alpha擷取、投影實際pixels／points、`groundContact`接影、命中點offset／致死保留、新makeArch／previous-current掃掠均開始落檔；不是只新增profile。renderer與弧接觸完整接線仍作者製作中，不把未完成段先說通過。

具體退回：projectionCache只用pose／xy／方向／長度作key，卻保存pathClear裁牆後的mask；同actor同姿位換world或prop破壞可能重用舊裁影與接觸點。已交combat最小修裁牆失效，QA補同位置world／blocker對照。另每alpha pixel呼叫pathClear是可見熱點，請用正常短局計數／耗時判定，未有實測不擴效能重構。

時間收斂：主core為人物影／真接影／原地束縛／群片／高拱，首縛暫緩，不再研究或增加prototype花樣。必要安全、新自然與正常桌機手機實物通過即結案；若真功能／效能阻擋影響主代理45–60分鐘估時即回報，不以無限重跑代替交付。

### 8351正常Lv1首段產品實看

總監真點最新8351鹿丸／開局，未改HP／XP／敵潮／clock，親看原生畫面：鹿丸當格人物alpha影＋窄黑接線，906敵人用自己的Walk alpha而非複製鹿丸。首次hurt ledger為ground-alpha，記真影接點、bodyKey與906/Walk.png來源；HP235、零pageerror。約3.125牆鐘秒推6.37遊戲秒（正常倍速2），起始未見實測效能阻擋，不外推高配手機。

快取已讀到world／revision／path／block key與每sim beginFrame，首段退回有實質修正，待QA同位置障礙／world反例。弧已接previous/current、細步推進與sweptBody後才hurt，仍待真掃掠反例及完整演出。此首段實物可用，不算完整候選；掌片／四向高拱／新自然與手機關仍未放行。

### 真卡／融合兩個反例及獨立重驗

已讀QA geometry-report，alpha／world-blocker快取／arch slice通過；最初快取退回解除。其後core真卡曾穩定失敗，總監用同CORE_SETUP在新context獨立復現四組visited=0：前沿與最近實opaque pixel只差約1e-14，尖端零寬嚴格邊界使接影漏掉；不是降期望可解。另指出捕到第二近靶後投影轉向群中心，凍結舊contactOffset可能落到透明處。

combat最小修：polygon邊界加1e-6世界單位數值EPS，未增攻擊半徑；每sim既成端點只在當前真alpha內重錨合法liveOffset並同步後段來源，不補傷，無合法點即斷束；致死原始contactPoint保持不變。

總監已新context獨立重跑：rank1/Q0=1真hurt，rank2=2，Q1=2，Q2=3；每個已捕末點都Ref.contains當前alpha=true且held=true。真卡／融合這兩項阻擋解除，原失敗保留為反例，未改測試期望。餘弧接觸／取消與新自然／正常手機仍由當次實物核證，未總放行。

最新core-report已直接讀：groundAlpha／fusion／archHurt全部通過、sourceStable=true。6筆真影縫hurt均在descent（progress約.86／.94／.96），兩輪各三靶、沒有同輪重打；不是按展示時計直接扣血。高於body高度零傷由geometry slice對照，真接觸ledger含xyz-tip-sweep與當格body來源。此核心幾何關可用，仍不代替新原生／自然與桌機手機實看。

### 整合來源與安全關更新

已核本樹HEAD `86e86b9d`：主代理整合新core `307f23bc` 與外部已發布 `bef89915`，保留外部Naruto；入口衝突由make重生，module／geometry未為merge改動。foreign原有CRLF warning不在本任務清理，也不聲稱全部清零。

最新core-report六組groundAlpha／fusion／archHurt／safety／stationary／readOnly已獨立讀到全過、sourceStable=true。merge後只fresh受影響入口／技能資料確認再收新自然，不因外部提交擴全套。當前無新增code阻擋，發布仍等當次正常自然、掌片／四向高拱完整原生與美術／動漫獨立實看、正式包及公開核對。

### 新產品自然與原生片獨立核證

已直接讀 `qa/reference-redesign/natural/report.json`：commit86e86b9d、runtime3617f40d…，sourceStable=true、errors空；從正常Lv1真鍵盤／真卡，75.44遊戲秒Lv7、6次已套卡、Q1、HP205.61／235存活，newCoreComplete及groupEver為true，20筆影縫原生hurt。未改HP／XP／敵潮／clock，沒有拿prototype展示tier當成長。

總監親看融合敵自身投影、arch-overhead／actual-descent-hurt／arch-full-recover原生相位，另以ffmpeg記憶體解碼當次片wall14.65／15／15.4秒（HUD27→28），確認當段真播放推進、人物可自由移動、下降94傷後回到地影／下一輪。50／94等數字以moveId／geometry ledger區分，不把overhead畫面上其他技能傷害誤稱弧提前命中。

動漫已另獨立看新桌機／手機入口及自然wall14.2起12fps24幀、38.5起4fps8幀，明確回覆人影接影／融合掌片／同影高拱下降的身份與動作無阻擋，見 `redesign-anime/runtime-review.md`。新自然核心／動漫關解除；總監無新機制阻擋，待美術當輪40px四向／完整窗口結論，以及主代理正式包／公開核對，不再擴研究或長局。

以下為研究／prototype歷史：當時只確認方向A可進製作；現已由上方真產品候選結果取代。舊影形、材質、分數與測試不作本次完成依據。保留鹿丸身份、276原地束縛與逐步成長；舊renderer、完美圓池、五招模板、同步拖敵皆可捨棄。

## 實際來源與方案核證

- 已親看使用者三圖：`redesign-reference/user-{body-shadow,group-shadow,shadow-reference}.png`。主判準是人體投影拉長、各敵人物影融合為不規則掌片且保留指間地面、同一腳影長出純黑高拱尖影；不是圓盤射粗管或敵腳冰刺。
- 已親讀 `redesign-anime/references.md`，親看指定影片KiGKoWDE0u8的8–20秒、104–114秒密採樣：不規則本影接人物投影；平面細尖→前部鼓起→同影塊長出高拱→穿身。此片為使用者指定的非官方混時期剪輯，不冒稱官方上傳。
- 另親看官方／授權c7UDaDGKGVA概覽及130–145秒2fps，人物投影在地面／樹面接合；SHINOBI FILES只作人物蒙太奇，8aOV飛段終結的樹間細線／札屬忍具，不誤作影材質。官方完整收回／首縛解除仍不足，遊戲解除標本作改編。
- 已親看Aragami／Ereban實際trailer概覽及來源manifest，只借影地／形體轉換節奏，不借能力或資產；Hollow Knight未確認可用影動作，不替方向背書。研究足夠，不擴第4款遊戲。
- 已讀art `redesign-art/research.md` 三方向及 `redesign-gameplay.md`：**選A人體投影—融合剪影**。B黑島侵染弱化連續影模仿、C體積影獸易失身份，只保留其轉態啟發，不混成三套常駐材質。最小核心以影模仿／影縫兩空間行為成立；群掌片是已捕影融合，neck暫緩，不卡五招。

## prototype實看、退回與修正

實體：`redesign-prototype/index.html`、`prototype.js`；本機8348同路徑。總監真開頁、親讀隔離碼，桌機64px與390窄視窗40px實看，不只收作者回報。

| 項目 | 具體觀察與目前結論 |
| --- | --- |
| 人體投影 | 現有atlas alpha壓平、雙足接人物輪廓＋窄頸，較舊圓池／粗管有身份；可作方向A主底。 |
| 群控首版 | 曾像owner到中心巨大平滑黑楔＋向敵細絲，已具體退回。修後真看64／40px，改各敵人體投影朝掌腹交疊、有指間負空間、owner薄頸接入；近群方向成立。散群只薄接，不硬填凸包。 |
| 影縫首版 | 遠上方目標讓弧單調向上，像長fan；已退回。修後近距側向目標能看高拱／回落穿身，64／40px左右方向成立。 |
| 影縫上下 | QA舊40bbf版原生中／末段壓成黑柱，曾退回。最新sidebow改地面法線側弓＋高度，親看vertical40上／下contact、up formed；再用全新Chrome context加`?v=sidebow`真開40px/up/tier3/4.8秒，清楚三個開口C弓與負空間，退回解除。 |
| 最新動態 | 總監另實際點mode／tier／up，不seek，親看1.65→2.70→3.85秒：地影階段→前沿上升高過目標→C弓回落接身，形狀連續無random抖。不是把靜圖當播放。 |
| neck附研究 | 首版遮黑頭臉、胸橫條，不能稱完整首縛還原；可暫緩，不因此擴新素材／第五招，不阻擋A核心方向。 |

## 證據與來源界線

QA `qa/redesign-prototype/revised-group-sewing` 已有64／40px群近／散及影縫左右的首中末／收回和真RAF片；其中舊上下黑柱片不可當sidebow證據。最新定點在 `qa/redesign-prototype/sidebow-vertical/report.json`，prototype.js `d29210b5…`、sourceStable=true、零error、verify-vertical SHA前後相同，各尺寸只錄up/down兩段。影片沿用four-space檔名不代表重錄四模式。總監已核來源並完成上列最新實看，未混稱舊片。

**prototype不載Combat／Player／World，A/B接觸由展示時間、tier由選單決定；沒有真傷害、AI拘束、卡牌或生命周期。** 因此它能驗方向、比例、投影與動作可讀性，不能驗真命中、自然養成或角色完成。276在prototype只是人物原地展示，尚不證產品控制已接好。

## 總監結論與下一關

總監對方向A與當前小prototype無未解核心視覺阻擋，**可進有界產品製作**；art最新獨立播放結論另由其lane交主代理。現在不再加來源、素材或整角色SOP，也不以功能零錯誤／分數替玩家說美感或好玩已認可。

若主代理進入產品實作，下一關才是真當格身影／前沿與碰撞共用、A真接影後B、原地束縛／牆／回呼取消、融合掌片不偷算空白AOE、立體拱影真接觸與逐步成長。這些尚未由視覺樣品完成；產品與發布保持未完成，當前材質候選不發布。
