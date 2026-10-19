# 可替換的多人連線接口

後續工作與獨立測試順序見 [多人連線 TODO](MULTIPLAYER_TODO.md)。

## 本次範圍與重構順序

1. 先以 `node tools/test_multiplayer.js` 固定既有訊息路由、關閉連線與停用中繼的行為。
2. 將既有 Firebase 房間與 WebRTC 傳輸改為明確建立的 adapter，取消載入時自動啟用。
3. 由穩定的 `G.Social` / `G.Net` 接口維持 UI 和 `G.Coop` 的呼叫方式；以
   `G.Multiplayer.configure({ rooms, transport })` 選擇 adapter。
4. 加入無後端預設值、切換生命週期、事件解除訂閱與 provider 無關的連線狀態。
5. 使用記憶體測試 adapter 驗證替換、房間與訊息傳輸，再重建公開入口。

這一步不加入外部服務或套件，不啟用 Firebase，不改合作戰鬥協定，也不提供對局中熱切換。

## 邊界

- **rooms**：多人身分、房間成員、開房／加入／離房、開始後關閉入場、遊玩狀態。
- **transport**：開啟連線、同步成員、定向送訊息、收訊息、狀態事件、關閉連線。
- **G.Coop**：原有房主權威、角色狀態及戰鬥事件；不依賴 Firebase、WebSocket 或 WebRTC。
- **G.DB**：本機／雲端存檔獨立於連線服務。啟用多人不代表啟用雲端存檔或排行榜。

預設未設定 adapter；單人仍可遊玩，多人接口回報不可用，不會建立網路連線。

## 設定方式

在 `js/net/multiplayer.js` 載入後、第一次使用多人功能前執行：

```js
await G.Multiplayer.configure({
  rooms: myRoomService,
  transport: myTransport
});
// 在房間外更換整組實作；兩者必須使用同一套 uid、room id 和 host uid。
await G.Multiplayer.configure({ rooms: otherRooms, transport: otherTransport });
// 在房間外停用。
await G.Multiplayer.configure(null);
```

`configure` 是非同步方法，必須等待完成。會驗證接口、關閉舊傳輸並等待舊房間服務
`stop('switch')`，解除舊訂閱，再安裝新實作。房間、傳輸連線或合作對局仍開啟時拒絕切換；
先正常結束遊戲、離房，再切換。原先註冊在 facade 的 UI／遊戲訂閱會保留，舊實作的延遲事件會被忽略。
尚未完成的房間服務操作也會阻止切換，避免加入舊房間的請求在替換後才完成。
新 adapter 必須沒有開啟中的房間／連線；若事件訂閱初始化失敗，清理新實作並退回停用狀態。

## 房間服務合約

必要狀態（getter 或屬性）：

| 狀態 | 格式 |
| --- | --- |
| `uid` | 尚未初始化為 `null`，初始化後為字串 |
| `me` | `null` 或 `{ uid, name }` |
| `started` | 初始化是否完成 |
| `room` | `null` 或 `{ id, host, isHost, open, members }` |
| `room.members` | `[{ uid, name, dex, shiny }]`，房主排第一，最多 4 人 |
| `available`（選用） | `false` 表示暫不可用；省略表示已配置可用服務 |

必要方法：

| 方法 | 回傳／責任 |
| --- | --- |
| `start()` | Promise：`'ok'`、`'need-nick'` 或 `'off'` |
| `stop(reason)` | Promise：離房、取消網路監聽／計時器、清除身分；可重複呼叫 |
| `claimNick(name)` | Promise：`{ ok, error? }`，成功後更新 `me` |
| `createRoom()` | Promise：建立並回傳房間，更新 `room` 並發送 `'room'` |
| `joinRoom(id)` | Promise：`{ ok, error? }`，成功後更新 `room` 並發送 `'room'` |
| `leaveRoom()` | Promise：離房、更新 `room = null` 並發送 `'room'` |
| `setOpen(bool)` | 房主開關入場；維持原有同步呼叫方式，實作應自行處理網路錯誤 |
| `refreshMember()` | 同步本機選用的角色資訊 |
| `setPlaying(bool)` | 更新遊玩狀態 |
| `on(fn)` / `off(fn)` | 訂閱／解除 `fn(eventName)` |

事件使用既有 `'room'`、`'room-closed'`、`'stop'`；資料必須先更新再發送事件。
`setOpen`、`refreshMember`、`setPlaying` 不回傳待呼叫端等待的 Promise。

好友、邀請、雲端公開個人檔案不是必要能力。選用接口為原有
`request`、`accept`、`remove`、`invite`、`acceptInvite`、`declineInvite`、
`refreshPresence`、`publishProfile`、`getProfile`、`friends`、`invites`、`now`。
未實作時讀取空列表、回報不支援或安全略過；本機 `profileData()` 仍正常運作。
目前 UI 仍是好友邀請入口；日後房號 UI 直接使用 `createRoom` / `joinRoom`，不需改傳輸或戰鬥。

## 傳輸合約

必要狀態：`uid`、`hostUid`、`isHost`、`open_`。開啟時的 uid 必須與房間服務相同。

| 方法 | 責任 |
| --- | --- |
| `open(roomId, isHost, hostUid)` | 同步啟動連線，不等待網路握手；相同房間重複開啟應無副作用 |
| `close()` | 關閉 socket／peer／監聽／重試計時器，且可重複呼叫 |
| `syncMembers(uids)` | 同步連線對象；由 adapter 自行決定星狀或伺服器中繼拓撲 |
| `send(toUid, message)` | 傳送 JSON 相容物件；序列化由 adapter 處理 |
| `peers()` | 回傳目前連線對象 uid 列表 |
| `mode(uid)` | `'connecting'`、`'connected'`、`'failed'`、`'closed'` |
| `slow(uid)` | 是否使用低頻同步；不可依賴傳輸技術名稱推斷 |
| `on(fn)` / `off(fn)` | 訂閱／解除 `fn(fromUid, message)` |
| `onPeer(fn)` / `offPeer(fn)` | 訂閱／解除 `fn(uid, mode)` |

`G.Net.toHost` / `broadcast` 由 facade 統一路由。訊息需要可靠、有序傳送；WebRTC adapter
使用可靠 DataChannel，WebSocket adapter 可利用其有序傳送。狀態快照、攻擊事件與
`{ k: 'start', seed, host, members }` 的內容沿用 `coop.js`。
Adapter 必須驗證遠端身分與房間權限，不能信任訊息中自稱的 `fromUid`。
`stats` 可選，保留既有除錯用計數器。

Facade 事件訂閱會回傳解除函式，也保留原本的 `off` 呼叫方式。

## 舊實作與驗證

`G.createFirebaseSocial()` 與 `G.createFirebaseTransport({ getSession })` 是保留的舊實作工廠，
載入不會自動選用。`getSession()` 需明確回傳自行擁有後端的 `{ uid, rtdb }`；
本分支 `G.FIREBASE_CONFIG` 仍為 `null`。不要填回上游專案。

```sh
node tools/test_multiplayer.js
node tools/test_i18n.js
node tools/build.js
```

測試使用假資料庫及記憶體 adapter，不連外。真實跨網路連線、部署與服務額度需在
選定並實作後端 adapter 後另行驗證。
