# 斑重製：現行架構的玩法差異缺口

2026-11-06。只讀產品程式的架構審查；不評分，不以安全／生命週期驗證代替角色品質。下列行號對應重製前的本次工作樹。先前 code-review 的範圍是傷害安全及接線，沒有證明技能形成有辨識的玩法；使用者已否定初版品質，舊驗收不能支持繼續沿用其玩法結論。

## 同模板的具體程式證據

| 現行事實 | 玩家能察覺的缺口 |
| --- | --- |
| `.omx/naruto-madara.js:20` `profile()` 把體術、豪火、須佐都設為 `4 + rankIndex` 次，僅分 interval/charge/range/arc；三者同走`:126` `advanceAction()` 的 while，呼叫`:109` `pulse()`。 | 三種能力實際都是「本體位置、最近可達敵方向、扇面全體立即扣血、末段1.65倍」。手腳接觸、向外傳播的火牆、具身巨刃的掃動沒有各自的空間／接觸規則。 |
| `pulse():111` 每段重新取 `origin=clone||owner` 並重選最近敵；`:112` 以距離及角度一次收集整扇面。 | 火幕第一波就能打滿整個射程，沒有火頭推進；須佐沒有手臂／刀鋒接觸路徑。換目標會讓整片扇面瞬間換向，玩家繞場不產生火線與刀線的不同決策。 |
| `poseFor():179` 體術和須佐共用同一局部時間公式；`:205` 須佐模型僅在 `s.action.kind==='susanoo'` 才顯示。 | 巨神像是同一次身體攻擊的外皮，沒有獨立現身、護衛、積勢／拔刀與回收時鐘；多段動作雖重新播放，仍未形成新機制。 |
| `profile():27` `meteorCount:2` 永遠固定；`:29` quantity vector 是「隕石2、衝擊波N」；`:143` 兩次 `rock()` 後，`:146` 以同一固定圓心追加0.35倍範圍傷害。 | 隕石確有獨立落地與預告，這部分不能說成假傷害；但數量卡主要是在落地後增加同一圓的扣血頻次，沒有增加天體、落點或雙星先後局面的變化。 |
| `update():159` 木分身每次固定選第一個已學技能：須佐→豪火→體術，再走同一 `action()/advanceAction()/pulse()`。 | 學須佐後所有木分身永久只用須佐。它們有真實位置與傷害，卻沒有前線／側翼／壓火等軍團分工，也沒有本體與軍團的接力條件。 |

## 成長有真收益，卻多為數值放大

`.omx/naruto-madara.js:32` 全招共用四階 `dmg` 1.2／1.45／1.75／2.1，射程等差增加，radius等差增加；`:23` 只讓各階多一次pulse。這些真實傷害及段數不應否認，但沒有階段式解鎖新的攻擊行為。

- 體術：range105→165、4→8段；沒有新的接敵、側移、換位、真接觸或撤退回應。不能因先前修短射程就稱為有體術循環。
- 豪火：4→8波、射程／傷害增加；`pulse()`仍是立即全扇面，沒有火幕推進／殘留線／分流或與其他招的可追溯連動。
- 須佐：4→8斬、射程／傷害增加；沒有肋骨→半身→完整體等功能差異，模型高度在`:205`只加 `rank*10`。
- 隕石：雙星及同圓衝擊次數增加；沒有改變敵潮被誘入落點的方式，兩顆也沒有分別承擔不同局面作用。
- 木分身：2→3→4名及100%→210%火力；rank2/4已有修正後的真傷害受益，但只放大原攻擊，沒有新的陣形／交錯施術／接力角色。

## 單一排隊會吞掉少量投資的招式差異

`canCast():101` 所有招共同要求 `!s.action`；`cast():103` 全部寫同一格；`tick():171` 有action直接返回，`:173` 反轉 moves 陣列後選第一個可施放者。這個優先度其實來自玩家學招的插入順序，並不是可靠的「重技策略」。正常按門檻學習時，後學的須佐優先於豪火與體術。

可以直接由公式構造反例：五階須佐加四張數量卡到16斬，duration為 `.32 + 15*.27 + .25 = 4.62秒`；CD是 `7.5*cdMul`。當 `cdMul<=0.616`，這次須佐收勢時自己已再就緒，反轉優先度又選須佐。隕石／召軍偶爾插入較高順位，豪火與體術則繼續等待。這不是實玩FPS測量，而是程式公式的排程反例；即使命中測試全部成立，也不能證明卡牌使整體循環變好。

即使尚未到上述臨界，數量卡也會把須佐佔用body從1.38秒拉到4.62秒，把豪火拉到3.45秒。增加一招段數同時推遲別招，且HUD僅寫「待出手」(`:225`)，沒有說明輸出交換。這是必須拆時鐘的原因，不宜再用更大數值補償。

## 以當前其他角色說明缺少的機制層次

| 現行實作參照 | 真正不同的機制，及斑可學的邊界 |
| --- | --- |
| 手鞠 `.omx/naruto-temari.js:34` `mastery()`、`:66` `snapshot()`、`:83` `start()` | 三輪普攻節奏會產生 empowered，並連到實際反彈budget；重風另有pushDistance/arc。`:143` waves、`:146` storms、`:155` summons 是不同實體，`:624` 分別advance；pose優先沒有鎖死已釋放風與夥伴。斑需要同等「動作顯示與戰鬥時鐘分離」，不照搬三星數值或反射能力。 |
| 小李 `.omx/naruto-lee-pursuit.js:51` `start()`、`:61` `advance()`；`.omx/naruto-lee.js:34` `retreating()`、`:306` combo排程 | rush與接觸攻擊分段，玩家移動／撤退會取消不合意的自動接敵；蓮華有綁定、拉近、升空、連擊、下降、重摔的狀態，不是相同扇面多打幾次。數量增加時comboDuration會縮、接觸節奏加速，沒有把角色單純鎖更久。斑體術至少要有接觸及玩家意圖契約，不強制套李的位移／無敵。 |
| 鳴人 `.omx/naruto-clones.js:77` actor、`:147` 每技cooldown、`:155` claimed目標分配、`:160` 接近與螺旋丸接觸 | 真分身有每技時鐘、依技選擇、分散搶敵及不同射程／接近邏輯；斑軍團不應永遠取一個最高順位同模板。`.omx/naruto-summoning.js:156` update在rank2刀斬、rank4油火、rank5變身狐狸有新增動作與真傷害分支；這才是成長改變局面，而非模型每階長10像素。 |
| 乙骨 `.omx/jjk-yuta.js:26` state、`:98` canCast、`:245` queueResonance、`:252` duetStrike、`:366` startRelease | body/speech/rika/release各自存在，里香travel→strike→return，本體與里香有兩個真起點；共鳴由真連擊結果排入，而非額外固定CD。顯現結束／恢復與放出仲裁明確。斑應建立自己的guard/army/field關係，不能照搬里香單夥伴或再做一個共同鎖。 |

## 最小沿用邊界與必拆時鐘

保留事件和存檔／卡牌接點，不保留統一扇面演出假設：

1. 沿用 roster ID30016、skill IDs、學習門檻與卡牌管線；`.omx/jujutsu-growth.js:204` registerQuantityConsumer可為每個新行為登記真消費端，預覽讀同一能力資料。數量卡不是一律延長body動作；應各自對應接觸、火頭／火線、guard斬擊事件、落石／落點或army實體，上限滿後照既有eligible排除。
2. 沿用 `.omx/combat-pulse.js:11` create與`:23` apply的owner/world/epoch、每段索引、targetIsLegal及landed secondary來源。每個body、guardian、field、army攻擊各建獨立cast／channel，避免來源去重。沿用World path對prop自身例外、其他牆阻擋、每目標取消重查。
3. **body時鐘**：只擁有斑本人可見的近身出手、結印、吐息／釋放和收勢；玩家撤退／移動改變什麼必明列。已放出火線不能繼續霸占body；圖集pose只表示此時鐘。
4. **guardian時鐘**：須佐有自己的顯現／蓄刀／掃擊接觸／回收，起點綁本體，碰撞跟當段刀線；不可因guardian活動就令全部body技能canCast=false。若有本體不可同時結印的短窗口，按指定相位仲裁，不是整招通用互鎖。
5. **field時鐘**：吐出的火幕與鎖定後隕石保存釋放位置、方向／落點，有獨立傳播、落地、留場／消散事件。移動能誘敵、換角度，已結算痕跡保持當次位置。field成立不能反過來不停重選最近敵而改寫既定地面局面。
6. **army時鐘**：軍團有穩定actor身份及個別phase、目標／位置／施術時鐘；具體分工由新企劃定義。事件回報可觸發guardian／field接力，但衍生不可無限遞迴。禁止用一個s.action替全軍排隊，亦不以無界並行同屏堆效果替代契約。

共同pause/death/world/epoch與clear仍由owner隔離；body pose、guardian pose、每個army pose與field進度各可查詢，繪製只讀。凍結／控制是否停已釋放場域需先寫契約，不能直接沿用初版 `owner.frozen` 讓全部時鐘停住而未說明。

以上只界定可沿用的可靠底層與需要重製的角色架構；具體能力、原作動作與成長選擇交企劃／動漫／美術互評，驗證必加入同成本自然成長及多招同時存在的排程觀察，不能再只測每招隔離靜靶。

## version2初稿：機制複核進行中

戰鬥作者通知完整初稿落地後才開始本節；編輯中的profile／尚未提供的美術API不當作最終失敗。新初稿 `.omx/naruto-madara.js` 確實改為 `s.body`、`s.guardian`、`s.fires`、`s.flames`、`s.meteors`、`s.pressures`、`s.army`：`canCast()/tick()`讓guardian與body並存，body以readyAt等待時間排序，fire前緣的previous/current距離與每面hitSet獨立。這些是實際程式分支變更，不能再稱為舊pulse換名字；仍需查下列未成立的因果。

已向作者、總監、根代理及測試直接提出：

1. **勢能歸屬**：初稿 `gain()` 只排除 `f.actor`（木分身），玩家自身分身作為合法owner時 `f.actor=null`，仍可能蓄勢及變完成體。須明確排除 SelfClones owner，不只木分身。
2. **末接觸條件**：`basicStep()`末接觸判斷讀整輪 `f.hitEvents`，前段命中／末段撤退打空也可給勢能；須依該末段真primary結果。作者已主動自查此處，未將半改狀態當最後結論。
3. **殘岩接力可達性**：`advanceFront()`只核火面幾何覆蓋殘岩，未核火源到殘岩的path，可在牆後殘岩圓心引爆；必須是真可達火接觸。衍生爆發不再呼叫gain／relay的方向正確，仍要補實際接觸門檻。
4. **雙岩／碎岩因果**：初稿 `emitMeteors()`開招即預排全部碎岩，`advanceMeteor()`第二顆未要求第一顆落地／殘岩成立；相較短合約「第一顆留下物體、第二顆砸出碎岩」，目前是同中心時間排程。需由simulation落地事件建後續物質來源，不能靠draw或預告存在替代。

還在核對：體術是否真正掃過接觸而非一條抽象長膠囊；踢掃不得繞過authored foot socket；guardian刀線與可見劍需同一transform及相位；四方向身體圖若仍朝右，不可只旋轉socket造成上下隔空傷。新atlas尚在製作時不以fallback當四方向驗收。測試須針對上述真反例，不用新profile存在或安全回歸數量當完成證明。

### 初稿修正後再查

作者已修並經獨立重新讀碼確認：gain/transform排除玩家自身分身；體術末段比對該段前後primary累計差；火前緣接殘岩加入path；開招只生成雙主岩，第一岩落地設firstLanded，第二岩落地事件才releaseFragments。各技能metrics/growthText已改讀真接觸半徑、接敵步幅、火面寬／推進、形態／劍壓、碎岩與軍團分工，不再假稱legacy m.range是實際射程。

但截至這次複核仍有具體退回項，已與總監一致直接告作者：

- **P0：踢掃的時間因果仍錯。** `basicStep()`把三條aim徑向線改成socket的progress `.2/.5/.8`，卻仍在一次接觸事件內全部命中；這只是換端點來源，仍會在當前可見腳尚未到達時預打未來腳位。需要像guardian一樣，逐simulation步取得實際前後pose/socket、共用該接觸段hitSet，僅掃已走過的軌跡。其他掌／肘接觸也須用當時draw選格／transform，不靠強塞phase/contact與progress=.5自認同步。
- **碎岩的可見物質來源未成立。** releaseFragments現在由次撞事件觸發，事件因果已有修；但fragment仍只存落點x/y與delay，draw沿各落點上空垂直降落，沒有撞擊中心→飛散→落點的來源軌跡。它仍可能被看到是再召天降小隕石。需parent source、軌跡與draw共用，與動漫正常相位審閱一起判定。
- **尚待新美術API驗證的P0：同一world transform。** `socketFor/avatarSocketFor`與draw本體／劍刃必同源，不能只同phase；方向上下的可見肢體若仍朝右，而碰撞按aim旋轉，就會隔空傷。這是候選完整atlas的必要驗收，未把舊fallback當最終產品結論。

再一輪作者已移除basicStep預掃，改 `advanceBasic()`逐simulation相位，碎岩亦加入 `sourceX/sourceY`、`flightProgress`與高度，draw由次撞中心飛往各落點。以上原退回項已有實質結構修正。繼續發現兩個範圍很窄的真sweep缺口，已直接同步作者／總監：

- 前一socket仍以current actor.xy及old progress重算，移動時不是上一simulation的世界位置；需保存每segment上一個實際world socket，下一步對它掃至本次socket。
- 直接切換bodyPose.index會丟前接觸窗尾。例如8段、duration=.80，interval=.0775，第6踢掃在.625秒的progress約.774，下步.650已換index，舊段到end=.85的已發生軌跡未結算。需跨界時先掃已過去的舊窗末端並finalize，再初始化新段；不能恢復成預掃未來端點。

這兩項須用移動本體與高段數真接觸反例修查，靜止pose對齊不足以證明完成。

作者再修後已獨立讀到：`advanceBasic()`按oldAge→newAge逐segment重疊窗口，先處理已過去的前段尾端才切新段；每段保存previousPoint實際世界socket，下一simulation掃到新socket。原先預掃、跨段漏尾與移動時重投舊端點的窄分支已有相應修正，測試作者已接手動態反例。

socket座標另與根代理／美術對齊：simulation的authored.y加height/2可能是「可見攻擊點對敵人身體中心」到ground座標的投影，不能僅因常數32就直接判錯；guardian亦同。必須由美術API明示visual／ground／目標身體平面，並用不同大小敵人的實際sprite接觸核對；若API已給ground則不能再補一次。此項仍等新runtime實際接線與四向畫面，未以開發fallback放行。

### 新runtime接線後的獨立實測

已實讀11KB新runtime，`pointFor()`與paint使用同frame.anchor／scale／mirror；API明示 `space:'visual-world'`。上下體術有bodyDirections獨立圖，非把側面圖的socket偷偷旋轉。第一個真整合問題由最小runtime fixture重現：kick progress=.7時，draw的bodyPose用recover取得taijutsu frame7，simulation私造contact取得frame6，sameFrame=false。作者其後共用basicPoseFor；再讀碼確認draw與simulation已同contactStart/contactEnd選phase。

以正常入口選斑／開局，注入原生受控Enemy(r14.08)、rank2體術與固定零移動輸入，獨立執行整輪.9秒（未變傷害／socket／碰撞）：

| 起始距離 | 右／左命中 | 上命中 | 下命中 | 本體自動前進量 |
| --- | --- | --- | --- | --- |
| 35 | 各4 | 3 | 3 | 0 |
| 45 | 各3 | 1 | 2 | 0 |
| 65 | 各2 | **0** | 1 | 13 |
| 80 | 各2 | **0** | 1 | 28 |

不是要求所有方向每段同傷；不同肢體接觸造成段數差異可以成立。具體退回點是上方65/80靶被canCast接受，停步自動接敵卻依contactReach60-8固定停在剩52距，與上向實際socket可達不符，完整輪零命中、下輪仍可重複空打。已向作者／總監／根代理提出按當向真socket幾何決定接近停點與可施放距離，不能放大無形範圍假修。

目前guardian三形metadata尚未ready的form返回null，未把開發fallback當成刀線同圖或完成體實畫證明。

作者其後以 `basicApproach()`依當向四個真contact frame的socket計算接近空隙及停點，取代contactReach常數停止。已再次從正常入口獨立重驗原反例：up65/up80現在各有1筆真hurt，總位移約19.9／30，未放大無形半徑；right/left65仍各2hit，down65有2hit。down80改為拒絕cast，不再接受不可達的空打。另以反向撤退輸入axis=[0,1]對up65重驗，cast=false且player.xy維持0，未自動拉回敵群。原auto engagement與撤退窄項已據真執行解除；各方向段數不同本身不作失敗。

測試作者亦回報特設對抗案例成立：未來腳位early零hurt／late一hurt；移動本體previousWorldSocket路徑真hit；8接觸第6踢跨.625→.650的舊窗尾真hit；正常同段23筆contact的socket sheet/index與draw一致。這些是特定時間與來源契約證據，不是整體玩法或美術通過結論。

另由本審查者獨立在正常入口執行rank1豪火、近150／遠450的原生敵人：.35秒皆零hit；.60秒近2／遠0；.90秒近4／遠1，body已解鎖而四面火仍活；1.50秒近遠各4、火面完成。真hurt紀錄有4個不同front castId。這支持「前緣有近遠先後、每面獨立去重、已放出火不霸占body」的窄機制，已不是初版瞬間整扇扣血；仍不取代火材質／吐息姿勢與正常成長整體循環審閱。

### 三形guardian新素材接線複核

三形及上下方向metadata到齊後，已獨立由正式runtime渲染3形×4向，並以API可見世界socket疊黃線／紅點，保存於 `rework-play/review-guardian-sockets.png`。實看肋骨手臂、甲胄握刀、完全體長刀與上下方向都有各自形體；線與端點貼可見手／刀口，左右鏡射對稱，不是把側圖socket旋轉。該圖是受控API縮圖幾何審查，沒有冒稱原生完整招式實錄。

再用正常入口與原生靜敵動態核對rank2甲胄：右／左／上150距，1.7秒各有2筆真hurt；每向各56個active-swing simulation樣本，g.blade對照draw所用avatarSocketFor（含同form/phase/age/progress/aim）在y+40投影後最大端點誤差0、frameMismatch0。側向使用armored，上向使用armoredDirections。down150的不可達目標被拒絕施放，沒有以假刀程補傷。上下形的可見刀端點另有上述API實看，不以此數字替代不同大小敵人sprite接觸與完整完成體演出審閱。
