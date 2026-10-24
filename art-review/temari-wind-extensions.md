# 手鞠風遁擴充交付

新增兩招，並重做演出，取代最初的細線風柱方案。

## 颱風迴旋（Lv.12）

巨扇揮出360°掃場，五階半徑240/270/300/330/360。被掃到的普通敵人以實際座標沿弧線繞風眼一整圈；每名自捕捉起有完整1.2秒，末段掃到者也不縮水。首領／精英／傳說／審判者不強搬，遇牆在安全點釋放。

每輪風流floor(1.25^Q)，每股每敵切割次數＝基礎3/4/5/6/8＋學會精通後的L＋Q；不同風流傷害獨立，同敵僅一份軌道位移。前緣正轉、敵人逆轉形成真實交會，避免高數量只增加外觀。主機控制實際位置，客端同步。切招保留已釋放技能，死亡／換場／分身移除釋放。

人物新增8格前／側／背真實轉身；另新增8格米白灰風刃。手鞠現用metadata為64格＝原48＋轉身8＋風刃8。高數量合併演出層而不合併傷害；保留中央留白、接地碎屑和尾段帶怪風痕。獨立視覺審查91分。

## 返風壁（Lv.15）

碰壁的全部敵方遠程類型可反打，包括首領／原先不可攔截彈、光束、遠程落點；近戰和環境傷害不變。反打數量、每道傷害、冷卻和分身繼續多軸成長。主機判定與反射來源移除，客端演出不產生第二份傷害。

## 程式與驗證

- 核心：.omx/naruto-temari.js、naruto-temari-reflect.js、temari-cyclone-vfx.js、temari-coop.js。
- 接線：技能圖鑑／學習池、圖示／HUD、施術姿勢、產生器／打包；原生遠程類型與網路來源ID；合法反射代理沿用既有百分比生命／擴散帳務。
- 素材：temari-spin-v1.png、temari-cyclone-wind-v1.png，提示詞／參考／雜湊存temari-cyclone-provenance.json及temari-provenance.json。
- 專項：tools/test_temari_typhoon.py、tools/test_temari_reflect.py、tools/test_temari_reflect_coop.py；既有手鞠與加權卡池回歸。
- 證據：.omx/state/temari-typhoon/report-orbit.json、coop-orbit-acceptance.json；.omx/state/temari-reflect/report.json、reflection-coop-report.json；各目錄視覺序列與verdict。

測試保持傷害數字開啟，正常推進原生FX生命週期，未藉隱藏數字美化畫面。多人驗證為兩個獨立瀏覽器執行正式協定、JSON測試傳輸，不聲稱外網WebRTC／丟包測試。手機為Chromium模擬，不冒稱實體手機效能。

原始風格參考入口：https://spritedatabase.net/game/55（Temari）。實際選用角色／風刃為imagegen新繪，未直接接入原遊戲擷取圖。廣域風術身份來源：https://naruto-official.com/en/news/01_1602；兩招的數值、位移與全類型反射為本作改編。

保留既有其他角色改動，不新增套件；復用傷害／碰撞／圖集載入與字體效果，未加入專屬傷害浮字彙總或重寫共用戰鬥。未commit、push或部署。
