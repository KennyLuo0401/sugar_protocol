# CLAUDE.md — Sugar Protocol

> AI 快速入門指南。閱讀此檔案後，你應該能在 30 秒內理解專案全貌，並在 5 分鐘內開始貢獻程式碼。

---

## 1. WHAT — 技術概覽

### 一句話定位

Sugar Protocol 是一個基於 **Sui Network** 的去中心化「言論族譜」系統，用 AI Agent 將非結構化新聞拆解為四層拓撲（Entity → Stance → Claim → Evidence），不可竄改地記錄在鏈上，並以 3D 力導向圖呈現衝突與支持的脈絡關係。

### 技術堆疊

| 層 | 技術 | 版本 |
|---|---|---|
| 智能合約 | **Sui Move** | Framework rev `testnet` (toolchain 1.64.1) |
| 後端 Agent | **Python 3.10+** | pysui, openai, beautifulsoup4 |
| AI 模型 | **GPT-4o-mini** (OpenAI API) | — |
| 前端 | **React 19** + Vite 7 | react-force-graph-3d, three.js |
| 鏈互動 (前端) | **@mysten/sui.js** | ^0.54.1 |
| 鏈互動 (後端) | **pysui** (SyncClient) | — |
| 部署環境 | **Sui Testnet** | chain-id: `4c78adac` |

### 專案結構

```
sugar_protocol/
├── Move.toml                  # Move 套件設定
├── Published.toml             # 已部署版本紀錄 (testnet)
│
├── sources/                   # ── 後端：AI Agent + 合約 ──
│   ├── core.move              # ⭐ 核心合約：SugarGrain 物件 & mint_grain
│   ├── sugar_protocol.move    # 空的佔位模組（未使用）
│   ├── agent.py               # 單篇新聞分析 Agent（較早版本）
│   ├── inspector.py           # ⭐ 主力 Agent：爬取 → 分析 → 遞歸上鏈
│   ├── chain_pusher.py        # ⭐ Python ↔ Move 橋接：型別轉換 & 交易執行
│   ├── batch_runner.py        # 批次執行器：多篇新聞連續處理
│   ├── prompt_lab.py          # Prompt 實驗場（開發/測試用）
│   ├── App.jsx.bak            # 前端 App.jsx 的備份
│   └── local_memory.json      # 本地去重索引（Entity name → object ID）
│
├── frontend/                  # ── 前端：3D 視覺化 ──
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       └── App.jsx            # 主元件：queryEvents → multiGetObjects → ForceGraph3D
│
└── tests/                     # Move 單元測試（6 個測試案例）
```

### 關鍵檔案速查

| 要做什麼 | 看哪個檔案 |
|---------|----------|
| 理解鏈上資料結構 | `sources/core.move` |
| 理解 AI 如何拆解新聞 | `sources/inspector.py` → `analyze_discourse_genealogy()` |
| 理解資料如何上鏈 | `sources/chain_pusher.py` → `push_grain_to_chain()` |
| 理解前端如何讀鏈 | `frontend/src/App.jsx` |
| 調整 AI Prompt | `sources/inspector.py` L19-33 或 `sources/prompt_lab.py` |
| 新增爬蟲目標 | `sources/batch_runner.py` → `urls` list |

### 已部署合約

```
Package ID:  0x3a89bbef10712247d2ef6bdf70ea9ea3c500182d060c6d507a0cfaf467cead75
Network:     Sui Testnet (chain-id: 4c78adac)
Upgrade Cap: 0x2cf092ff1ee6709fde80f9129a02d85f357e272ffb490d780f52acc302d0e839
```

---

## 2. WHY — 架構設計理由

### 核心領域模型：四層言論拓撲

```
L1 Entity       「比特幣」「馬斯克」           ← 核心主體，全局去重
    │
    ▼
L2 Stance       「看多」「看空」「監管壓力」    ← 對主體的態度/立場
    │
    ▼
L3 Claim        「MicroStrategy 再次買入」     ← 具體論點或事實宣稱
    │
    ▼
L4 Evidence     「Source: abmedia.io/...」     ← 原始出處 URL
```

**為什麼是 DAG 而不是 Tree？**
一個 Claim 可以同時引用多個 parent（`parents: vector<ID>`），例如一個論點可以同時支持某個 Stance 並反駁另一個 Stance。這形成了有向無環圖（DAG），而非簡單的樹。

### SugarGrain 物件設計

```move
struct SugarGrain has key, store {
    id: UID,
    content: String,           // L1-L4 的文字內容（統一結構）
    parents: vector<ID>,       // 指向上層節點（DAG 邊）
    bond_type: u8,             // 語意關係類型
    source_url: String,        // 原始新聞出處
    author: address,           // 提交者錢包地址
    timestamp_ms: u64,         // 上鏈時間
    purity_score: u64,         // 純度分數（目前固定 100，預留欄位）
}
```

**`bond_type` 語意對照：**

| 值 | 常數名 | 視覺 | 含義 |
|---|---|---|---|
| 0 | GENESIS | 🟠 橘色節點 | L1 根實體，無 parent |
| 1 | DERIVED | 🟢 綠色線 | 支持、延伸、事實陳述 |
| 2 | CITES | 🟢 綠色線 | 引用 |
| 3 | CONTRADICTS | 🔴 紅色線 | 反駁、衝突、對立觀點 |
| 4 | CORROBORATES | 🟢 綠色線 | 佐證 |

**為什麼所有 Grain 都是 shared object？**
因為言論紀錄是公共知識，任何人都應該能讀取。`transfer::share_object(grain)` 讓 Grain 成為全局可存取的共享物件，這也讓未來的預測市場合約可以直接引用。

### Agent Pipeline 設計

```
batch_runner.py          inspector.py              chain_pusher.py
───────────────          ────────────              ───────────────
                         ┌─────────────┐
URLs list ──▶ 逐一呼叫 ──▶│ fetch_clean_text()      │ Jina Reader → BeautifulSoup fallback
                         │      │                    │
                         │      ▼                    │
                         │ analyze_discourse_         │ GPT-4o-mini + JSON mode
                         │ genealogy()               │ → { entities[].stances[].claims[] }
                         │      │                    │
                         │      ▼                    │
                         │ get_or_mint_entity()       │ 查 local_memory.json 去重
                         │      │                    │
                         │      ▼                    │
                         │ 遞歸 mint:               ──▶│ push_grain_to_chain()
                         │ L1 → L2 → L3 → L4        │ pysui SyncTransaction
                         └─────────────┘              │ → Sui Testnet
```

**為什麼用 Jina Reader 而不是直接爬？**
Jina Reader (`r.jina.ai/{url}`) 會自動清理 HTML、移除廣告和導航，回傳乾淨的 Markdown 文本。這大幅降低了丟給 GPT 的 token 數量和雜訊。BeautifulSoup 只是備用方案。

**為什麼去重用本地 JSON 而不是鏈上查詢？**
效能考量。每次查鏈都需要 RPC 呼叫，而本地 JSON 的模糊匹配（`name.lower() in item['content'].lower()`）足夠應付目前的規模。未來如需多 Agent 協作，應改為鏈上 Registry 或共享資料庫。

### 前端讀取策略

前端不直接查 object table，而是透過 **事件索引（Event-based indexing）**：

```javascript
// 1. 查詢所有 GrainMinted 事件
queryEvents({ MoveEventType: `${PACKAGE_ID}::core::GrainMinted` })

// 2. 從事件提取 grain_id
events.data.map(e => e.parsedJson.grain_id)

// 3. 批量讀取物件內容
multiGetObjects({ ids: objectIds, options: { showContent: true } })

// 4. 根據 parents[] 建立連線，餵入 ForceGraph3D
```

**為什麼用事件而不是 owned objects？**
因為所有 Grain 都是 shared object，無法透過 `getOwnedObjects` 查詢。事件是唯一可靠的全局索引方式（在沒有自定義 indexer 的情況下）。

---

## 3. HOW — 工程規範與工作流程

### 本地開發環境設置

```bash
# 合約
sui client switch --env testnet
sui move build          # 編譯 Move 合約
sui move test           # 執行 Move 單元測試（6 個測試案例）

# 後端 Agent
cd sources/
python3 -m venv venv && source venv/bin/activate
pip install pysui openai requests beautifulsoup4 python-dotenv
cp .env.example .env    # 填入 OPENAI_API_KEY

# 前端
cd frontend/
npm install
npm run dev             # http://localhost:5173
```

### 環境變數

| 變數 | 用途 | 設定位置 |
|-----|-----|---------|
| `OPENAI_API_KEY` | GPT-4o-mini API 金鑰 | `sources/.env` |
| Sui active address | 交易簽名者 | `~/.sui/sui_config/client.yaml` |

### 合約部署 & 升級

```bash
# 首次部署
sui client publish --gas-budget 100000000

# 升級（需要 UpgradeCap）
sui client upgrade --gas-budget 100000000 \
  --upgrade-capability 0x2cf092ff1ee6709fde80f9129a02d85f357e272ffb490d780f52acc302d0e839
```

⚠️ **升級限制：** Sui Move 升級不能刪除或修改已有的 struct 欄位，只能新增函式或新模組。規劃新功能時必須考慮向後相容。

### 關鍵常數位置

修改這些值時需要同步更新多個檔案：

| 常數 | 檔案 |
|-----|------|
| `PACKAGE_ID` | `sources/chain_pusher.py:12`, `frontend/src/App.jsx:6` |
| AI Model | `sources/inspector.py:25`, `sources/agent.py` (GPT-4o-mini) |
| Event type string | `frontend/src/App.jsx` → `GrainMinted` |

### Git 分支策略（建議）

目前只有 `main` 分支，3 commits。建議採用：

```
main          ← 穩定版，已部署的合約對應此分支
├── dev       ← 開發分支
├── feat/*    ← 功能分支（如 feat/prediction-market）
└── fix/*     ← 修復分支
```

### 測試規範（待建立）

```
tests/
├── core_tests.move            # Move 單元測試（mint、bond_type 驗證）
├── test_inspector.py          # Agent 測試（mock OpenAI response）
└── test_chain_pusher.py       # 上鏈測試（mock pysui）
```

### 已知技術債

| 項目 | 嚴重度 | 說明 |
|-----|-------|------|
| ✅ `mint_grain` 是 `public fun` 非 `entry fun` | 🟡 中 | 已改為 `public entry fun`，加上 lint 抑制 |
| ✅ `purity_score` 無 mutator | 🟡 中 | 已新增 `update_purity_score` 及 getter 函式 (`bond_type`, `content`, `parents`, `purity_score`) |
| ✅ `doctor_raw.py` 命名混亂 | 🟢 低 | 已重命名為 `App.jsx.bak` |
| ✅ `local_memory.json` 模糊匹配 | 🟡 中 | 已改為精確匹配 (`==` 取代 `in`) |
| ✅ 無錯誤重試機制 | 🟡 中 | 已加上 3 次重試 + exponential backoff |
| ✅ 前端 Event 查詢 limit=50 | 🟢 低 | 已改為 cursor-based 分頁，抓取全部事件，multiGetObjects 也分批處理 |
| ✅ tests/ 為空 | 🔴 高 | 已新增 6 個 Move 單元測試（正常路徑 + bond_type 邊界 + purity_score 更新） |

---

## 索引：深入文件（待建立）

| 文件 | 內容 |
|-----|------|
| `docs/ARCHITECTURE.md` | 完整系統架構圖、資料流、sequence diagram |
| `docs/MOVE_CONTRACTS.md` | Move 合約 API 文件、struct 定義、升級規劃 |
| `docs/AGENT_PIPELINE.md` | AI Agent 詳細流程、Prompt 設計原則、token 預算 |
| `docs/PREDICTION_MARKET.md` | 預測市場擴展設計、AMM 機制、結算流程 |
| `docs/DEPLOYMENT.md` | Testnet/Mainnet 部署 checklist、金鑰管理 |
