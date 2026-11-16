# 指定參考重設計：當輪產品動漫驗收

範圍：隔離樹 `C:/Git/pokesurvivor/.omx/worktrees/shikamaru-reference-redesign`，8351正常入口、NarutoShikamaru version6。只檢人影接影、已捕目標投影融合、同影鼓起／高拱／下降身側；不新增來源研究、素材或首縛門檻，不修改產品與其他角色。

依據為使用者三張圖、指定KiGKoWDE0u8已實看片段與本次新runtime。舊prototype、舊QA、舊自然局及先前美術放行均不作本次完成證據。

## 已實看正常入口

獨立看過 `qa/reference-redesign/art-entry/desktop-normal-entry.png`、`mobile360-normal-entry.png`，以及 `art-native-entry/desktop-03.png`、`desktop-06.png`、`mobile390-06.png`。後組report明示normalEntry=true、fixture=false、version6、Lv1，對照遊戲時間9.34／15.23／13.69秒與當時phase。

- 鹿丸腳底投影已能辨出髮束／軀幹／身體的黑色剪影，由腳邊接出；不再是固定完美圓池外接紫脊管。
- desktop06可見彎曲窄影連到實際目標足底，目標保有自身黑色投影，符合 `user-body-shadow.png` 的「人物投影拉長接影」方向。
- 手機360／390仍看得到身體與腳底影的關係、可走路面；影沒有發光材質或管狀中心線。

上述畫面只證正常起手與連接，沒有用其代稱高拱下降／群體融合已完整看過。這一部分沒有發現需要退回產品的身份形態阻擋。

## 當輪新自然局與連續形態已實看

已獨立實看本樹 `qa/reference-redesign/natural` 的 `Lv1-alpha-source.png`、`real-ground-contact.png`、`fused-native-projections.png`、`arch-rising.png`、`arch-overhead.png`、`actual-descent-hurt.png`、`arch-full-recover.png`。再直接解碼同資料夾的產品原生錄影 `reference-new-core-native.webm`，親看wall14.2秒起12fps／24幀（HUD約26–30秒）與wall38.5秒起4fps／8幀（HUD約71–75秒），避免只憑相位名稱推論動作。

| 對照使用者參考 | 當輪畫面可見結果 | 結論 |
|---|---|---|
| `user-body-shadow.png` 及指定片8–20秒的人物投影 | Lv1影由鹿丸腳底連續接出，髮束／頭身黑剪影可辨；真接觸時連到敵方原生投影輪廓，不以範圍圈冒充影子 | 人影接影成立 |
| `user-group-shadow.png` 多敵不規則黑片 | HUD72–73秒幾個已捕目標的自身影連成不規則黑色實面，留有各自輪廓；不是全部候選怪預先一起鋪黑，也不是每敵另加同款圓圈 | 已捕投影融合成立；採影輪廓合併關係，不把參考中的掌狀負形生硬當一隻召喚黑手 |
| `user-shadow-reference.png` 與指定片107–114秒平面→高拱→穿刺 | HUD27秒，同一條地面影從身旁長起，拱過目標，尖端向下接身側；高密取樣看到上升／過頂／下降，並非只切換一張三角刺。HUD73–74秒亦可見有跨度的高弧與地面融合影同框 | 高拱的來源、空間與下降動作成立 |
| 收勢／維持因果 | HUD28秒命中後長弧離場，仍保留鹿丸本身地面影，玩家繼續走；新一輪接影不是讓所有黑影永遠掛在場上 | 回到地面影及下一輪銜接成立 |

當輪report對上原片：commit `86e86b9d0e2e452bdd3ba463a8ca3813c0f2ee5e`，來源全程穩定、errors為空；正常Lv1起，75.442秒到Lv7，六次真卡成本，敵潮／HP／XP／clock未改。已檢視真下降事件：game27.669秒、targetId7（104號怪）、弧progress .9532、接觸z35.177，實際HP由1降至-93；這筆資料只支持看見的下降命中不是展示假打，不拿數字代替形態。

驗收來源SHA256：runtime `.omx/naruto-shikamaru.js`=`3617f40d7036e25d363788855f2268f1540a3c8e0343e9f8e24076753b371ec3`；`reference-shadow-geometry.js`=`c456a3d702cc3627e34aa11a350ecce40976f8f3abb468dd0232ceccc2920560`；art=`a628d34bf34b196245e9e9c99f9a4b0d4e9a53a01221694087ca5c7e8b8a12aa`。

## 有界結論

**人影接影、已捕投影融合、同影鼓起高拱並下降接身側，均已在本輪產品正常入口／自然原片實看成立；動漫lane沒有未解真形態阻擋，可進可發布候選。** 沒有沿用舊prototype或舊放行，也未要求復活已藏首縛、重做其他Naruto、增加新素材或再找來源。這是對指定參考之身份與動作關係的判斷，不替使用者宣稱好看／好玩；原生片取樣不是完整逐幀播放或音訊聽評。
