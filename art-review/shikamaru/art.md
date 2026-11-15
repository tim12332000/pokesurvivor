# 鹿丸正式美術

## 產物與來源

- `shikamaru-art.js`：on-demand facade，唯讀取樣與繪製，模擬由combat持有。
- `shikamaru-frames.json` v2 與 `shikamaru/atlas-v1.png`：30個量測圖格。idle、交替雙腳跑步、結印三相各有前／背／側；投札三相前／背／側，左向鏡射側向；hurt、跪地、倒地。並非獨立八方向圖。
- `shikamaru/source-v1.png`、`source-v2-throw.png`：內建imagegen原始輸出，非官方擷取。兩份提示見同目錄 `prompt-v1.txt`、`prompt-v2-throw.txt`，後者參考前者保持身份。
- `tools/build_shikamaru_assets.py`：只量測原圖連通alpha輪廓與等比例打包，保留來源SHA256及裁切rect於metadata；使用既有Pillow/numpy/scipy，無新增依賴。

## 第一次獨立實看與退回

實看原始圖、打包圖及正常入口 desktop/390/360。鳳梨頭、木葉綠背心、深色褲與腳底都可辨；蹲/倒保持相同比例，沒有拉伸至站高。透明背景樣本alpha=0，隱藏RGB不作可見霧處理。角色腳下地面仍可走，HUD與五技能列未裁切。

退回：v1上下投札仍使用結印，僅側向有投擲三相；影捕捉/影縫同粗直帶。已留 `art-qa/verdict-v1.json`，不以素材完整替代動作成立。

## 第二次修正

imagegen補前/背投札起手、釋放、收勢，新增6格，sample trap四向接線。原圖上前向張手釋放、背向持刀掛札至伸臂皆非結印；動漫另獨立檢視原圖。戰鬥作者v3另將影縫改厚根收尖立體刺，影首縛沿身扣頸；本lane不改戰鬥draw。

正常入口 `tools/test_shikamaru_art.py` 重跑：desktop/390/360各pageerror=[]，dex30017、level1、ready=true；真鍵盤四方向截圖在art-qa。測試沒有加等級或改XP。此項只證入口與素材，不代替完整自然長局。

最終演出與影片相位獨立驗收待下節更新。未實聽音效，非手機實機長局。

## 最終獨立演出放行

已實看 `qa/trap-native-phases/native-trap-{down,up,left,right}-{prepare,release,recover}.png` 共12張原生RAF完成畫面。前向舉手持刀→張手→垂手、背向舉手→伸臂→垂手皆真在正式入口使用，不再套側向/結印。唯讀draw以當輪pose.aim決定攻擊方向；走路/idle維持Animator方向。這是最後一次純方向分派修正，未更改戰鬥數值/命中/成長。

另實看當輪 `native-final-cardinal`／`native-final` 影捕捉平帶、影縫接地三尖刺、影首縛沿身扣頸採樣，輪廓語意已分開。用Chrome真播放30.8秒原生影片，取5.34/10.57/15.80/21.11/26.38/30.8秒樣本；`art-qa/video-review.json`證currentTime持續前進readyState4至正常片尾。沒有成功seek主張，也未聲稱逐影格觀看。

Visual verdict最終pass 92（只作美術訊號，不替代樂趣）：`art-qa/verdict-final.json`，同步 `.omx/state/shikamaru/ralph-progress.json`。具體退回已解除；產品凍結。

最終補驗：另獨立實看 `qa/strangle-body-final/strangle-right-00/01/02.png` 首/中/末，bodyH=39的貼身錨點修正後上升位置貼合敵人，未再把扣頸畫到頭上方。新 `trap-phases-release` 的前背釋放/收勢亦看過，真實投向與上述12幀相同成立。這些是視覺錨點/分派定點補驗，非重新宣稱整局來源完全不變。
