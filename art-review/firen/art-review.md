# Firen 原版美術與動作驗收：通過

以經典 LF2 2.0a 原始圖格對照，Firen 火球、烈焰衝刺、噴火與爆炸四招的當次實際畫面均成立。沒有以選角圖、作者測試或舊角色通過替代完整動作驗收。原金髮、紅衣、深色褲裝、拳腳、手部蓄火、全身燃燒奔跑、口部連續噴火及紅光爆炸蓄力皆保留；無AI重畫或改色。

## 實作與共用來源

`.omx/lf2-firen-art.js` 是共用原版圖格渲染器的薄接點。經主代理授權，`.omx/lf2-boss-art.js` 僅新增拒絕覆寫既有角色的register功能、明示選用的投射物方向旋轉，以及Firen持續施術的傷害閃白優先序；不複製第三套圖格parser/cache/繪製引擎。既有Firzen／Julian預設行為及Julian103透明格優先序保留。

原body65px→world64px，仍使用每格centerx/centery固定錨點，不按蹲身／倒地外框放大。噴火271的原口部opoint(42,41)、center(22,79)，經同一sample/transform供繪製和戰鬥讀取。235/255/267/285分別為FireBall/Blaze/Inferno/Explosion，出手／接觸與獨立效果時鐘由戰鬥lane提供，draw只讀。

火球及噴火投射物明示rotateToAim：先移到真pivot(e.x,e.y-lift)，再按aim旋轉原圖局部座標，與每格ITR的前向／側向軸一致。人物、地火及爆炸不旋轉，舊角色沒有旗標的效果仍沿用原鏡射。實際上下與斜向原生probe已看，嘴部來源相接、火舌軌跡與目標方向清楚，沒有把整個人旋轉。

## 當次正式入口與自然畫面

獨立以真正選角／開始按鈕，從全新1100×850桌機及390×844手機瀏覽器進Firen Lv1。零頁面錯誤，四個學習圖示可見且在畫面寬度內，選中縮圖和大頭像正常，腳底與陰影相接，沒有彩色圖集邊框。證據在本機`.omx/state/firen/art-entry/`。

已實看手機自然局的Blaze釋放、嘴焰獨立飛行、Explosion高峰及收勢相位：角色燃燒奔跑和身後固定地火可分辨，嘴焰離體後繼續飛行；地火屬Blaze，不把Inferno虛構為常駐地火。爆炸短暫遮住本體，但周邊路面、敵方威脅與觸控仍可見，爆炸散去即回到原身體輪廓。另真正ffmpeg seek58.80秒手機原生影片的25／38／50秒並實看，見真觸控移動、原火球、留火軌跡、持續釋放及敵我相對移動；未聲稱逐秒看完整部影片或聲音聽評。

## 原生四招與具體修正

已實看當前`qa/firen/final-cycles/`的火球起手／釋放／收勢、Blaze燃身移動及熄火、Inferno口部火舌成長與收勢、Explosion109起勢→110接觸→煙／散去、獨立地火收尾等PNG。另真正從當前11.04秒`native-cycles.webm` seek5／6／6.4／6.7／7／8秒並檢視：發射、移動、口部噴火、爆發高峰和清楚的收束皆成立，不是靜圖拼接。這是Lv30／技能一階、高HP零傷害靶的受控原生片，與Lv1自然成長分開。

初版當次影片曾發現真實問題：Inferno接觸時受傷flash把可見本體換到hurt180，而還在出火的mouth socket取source271。已只對Firen正在施放的姿勢保留原cast frame並套原白色flash，死亡仍先於施術；無pose仍正常hurt，其他角色優先序不變。實際Chrome canvas證明hurt+cast+flash與cast均取271、2037個alpha像素完全相同且白flash全保留；普通hurt為180、死亡230、Julian鏡影103不變。修正後短原生片已重錄，`firen-final-cycles-source.json`為ok/errors空/sourceStabletrue；獨立重新計算全部非入口runtime／素材hash無差異。舊自然片若錄於純音訊／純美術修正前，只作其正確標示的自然流程證據，不冒稱每個byte等同最終候選。

visual-verdict.json為94/pass，沒有剩餘美術阻擋。這是來源、接線及可讀性驗收，不代表實體手機長局、多人網路、完整原LF2物理、玩家主觀好玩或真人音效聽評。
