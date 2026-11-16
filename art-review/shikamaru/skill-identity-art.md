# 鹿丸技能辨識：同尺寸看輪廓與段落

使用者反映影子各技能看不出差別；舊有機ABC的通過只證單根/接力，不可拿來回答這次辨識。範圍限shadow/sewing/strangle/net，不改單根ABC、腳底池、成長數值或札機制，不新增角色圖。

## 現碼診斷（不是尚未看的新片結論）

- `activeFor`在共享plan存在時只回shadow，finish才回strangle；真sewing施放沒有獨立身體窗口，因此即使`advanceSewing`有真傷，本體仍可能站影模仿/一般finish動作。
- 影縫effect原為life .36秒、三根48px升刺；高峰很短、身體與影模仿沒有接力姿勢，手機投影後易只剩一閃。不能以改技能名或圖示代替。
- facade net為Seal→Crouch，finish也Seal→Crouch→Idle，影縫fallback亦Crouch；三段都蹲結印，缺少不同的身體時序。

## 共同空間與時間合約

| 招式/段落 | 主輪廓與真事件 | 身體語意 | 必須與其他招不同 |
| --- | --- | --- | --- |
| 影模仿 | 貼地有機單根ABC，真命中後纏足/拘束；不升起大刺 | 站立Prepare→Seal，影已放出後可Idle/真walk | 地面連接與腳踝；不能用影縫尖刺替代普通命中 |
| 影縫 | 沿已接觸鏈，從敵腳底逐波立起厚根細尖的實體刺，穿過身側/軀幹高度後沉回 | 短局部窗口Prepare→低蹲施術→回Seal/Idle；每輪只借身一次，不每pulse重設 | 上下高度/真分波；峰值不是.36秒中極短一閃，不用同一縮環換色 |
| 收網net | 原鏈收緊，腳下束環由寬至窄、橫向繃直；只按真接觸出扣緊後果 | 站立雙手收束，保持Seal，與影縫低蹲分開 | 橫向/貼地，不長立刺，不冒充首縛握頸 |
| 影首縛 | 沿真bodyH從腳底盤身而上，肩頸處收緊，末段明顯扣頸/勒束，再落回影線 | 從低姿操影起身至站立Seal，再明確放手收勢 | 沿身連續上升/頸部收束，不畫三根刺、不只腳底一圈 |

VFX的主輪廓必須由實際施放/命中狀態取得；繪製不新建傷害時鐘。身體只借短真窗口，移動時長phase仍真walk，不能為辨識招式把撤退鎖住。若sewing窗口與net/finish衝突，共享net/首縛優先，sewing已釋出刺影仍按獨立時計完成，不能被姿勢取消。

## 接線與所有權

combat擁有VFX、事件與activeFor的真局部phase；art只擁有facade phase映射。建議sewing一次真cast記局部body時計，提供phase=sewing、phaseAge/phaseDuration/moving；不可每次draw猜時間，也不能每個命中重新延長身體。現有前/背/側Prepare/Seal/Crouch可表達以上差異，無需重生整圖。

影縫手機可讀性先做大主形/可見頂峰窗口、保留波次間隙與沉回；不以更多白粒子/紫描邊補。首縛以實際敵人體高定位頸，不統一往頭上50px畫。net縮環與影模仿足影不可全時常駐，以真phase/held區分。

## 當輪驗收

同尺寸、同成本、同敵體高，各取shadow、sewing、strangle首/中/末/消散與net短段原生片，另看360/390正常入口。必核真phase/真hit來源及body採樣鍵，不能把未學技能或另一招前搖標成該招末段。受控展示與自然局分開；既有ABC/成長測試沿用對應範圍，不大擴全SOP。

退回條件：sewing仍被shadow pose吞掉；手機只見一閃無實體立刺；三招都同一縮環/同一Crouch；首縛升到頭頂外不貼身；net畫成穿刺；移動時長蹲姿滑行。沒有具體問題就停止擴改；通過只證這次可辨契約，不代表真人已認可樂趣。

## 已落地的facade映射

combat已確認一次真施放`sewingPose` .55秒（非每pulse重設），phase/phaseAge/phaseDuration/moving直接供身體。art已接：sewing局部Prepare→低蹲操影→站Seal→Idle；net為站立Prepare→Seal；首縛僅真kind=strangle時低Crouch→站Seal→Idle，未學首縛的finish不假作首縛姿勢。這是低姿結印操影，並非素材沒有畫出的「雙掌拍地」。

moving sewing/net/finish等長階段一律真walk並保留移動方向，hurt/faint仍優先。回歸`node tools/test_shikamaru_art_phases.cjs`通過，含三招相反起身/蹲姿時序、net不再蹲姿、未學不冒姿勢與moving不滑行；語法檢查通過。這些只證取樣合約，仍等當輪真片/手機實看。

## 當輪獨立實物驗收：可辨差異與限制

證據為最新 `qa/skill-identity/native/{desktop,mobile360,mobile390}`，每尺寸同一四張真卡配置（shadow3/Q0、sewing1、strangle1）、相同三個近距百萬HP原生靜靶，正常shared RAF自動出招，未推clock。這是受控同成本展示，不冒充新自然局；native/report sourceStable=true、errors=[]。

已親看桌機shadow中段、sewing首/中/末/消散、strangle首/中/末/消散、net首/中/末/消散；360的影縫/首縛/net關鍵峰值，390的shadow首/末/消散、sewing身體/末/消散及新增sewing-rise、strangle-rise和strangle-last。其餘動態另真播放最新桌機4.76秒、360 3.96秒、390 4.00秒原生短片至ended=true/readyState4，親看播放採樣。`art-review/final-playback.json`保存每片SHA、當次讀取後檔案未改、currentTime遞增及片尾，不以舊重錄前片代替。

與舊版可見差異：

- **影模仿**仍是貼地單鏈ABC和足部纏繞，不靠新改色/新立刺假稱改善；其貼地輪廓提供另外兩招的高度對照。
- **影縫**不再每pulse生一份.36秒小effect。本輪是同cast/target唯一刺actor，下一輪前才重新起升、真hurt時在最高、短withdraw回地，第一/中/末波都維持一組而非疊成森林。手機主刺高度明顯高於敵人全身，白閃外兩側厚根/尖端仍可見。這不是單純「原來也有刺、現在仍有刺」；身體的真sewing phase/key=crouch也在middle資料與畫面成立，原先plan吞姿勢已解除。
- **影首縛**不再每.23秒真pulse重生.43秒另一手。現在同一條沿身上升的手臂/盤繞輪廓持續，後續真pulse收緊同手，末段不再跳回腳底重新長一隻；其貼身螺旋/握頸而非三根直立尖刺，與影縫可辨。手機主要靠沿身纏緊與釋放主輪廓，不把細小四指逐根可讀當完成條件。
- **net**仍是平地交叉影索/足底縮環，身體已與影縫相反，維持站立收束；其hit後下一招影縫可出現，所以`net-last`有另一輪正在升的刺，不能把那組刺錯標成net。首縛first同樣可能帶影縫收回，已核真來源，沒有硬剪掉合法接力。

實看影縫由低蹲至站印、首縛由低操影至站印後放手，時間軌跡與敵人效果配合；正常移動仍真walk。不以名稱/進度文字當主要辨識證據，也未更改ABC、池或成長來湊通過。

當輪四招/段落辨識合約無未解美術阻擋，可交主代理作可發布候選；未聲稱使用者已認可美感/樂趣。新verdict在 `qa/skill-identity/art-review/verdict.json` 與 `.omx/state/shikamaru-skill-identity-art/ralph-progress.json`，不沿用舊ABC/三角分數，不擴重拍完整自然局或新增素材。
