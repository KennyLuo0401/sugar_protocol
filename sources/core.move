module sugar_protocol::core {
    use std::string::{String};
    use sui::object::{Self, UID, ID};
    use sui::tx_context::{Self, TxContext};
    use sui::transfer;
    use sui::event;
    use sui::clock::{Self, Clock};

    // --- 錯誤代碼 ---
    const EInvalidBondType: u64 = 1;

    // --- 事件定義 (前端監聽用) ---
    struct GrainMinted has copy, drop {
        grain_id: ID,
        parents: vector<ID>,
        bond_type: u8,
        author: address,
    }

    // --- 核心物件: SugarGrain ---
    struct SugarGrain has key, store {
        id: UID,
        content: String,           // 原子宣稱內容
        parents: vector<ID>,       // 引用/反駁的對象 (DAG 結構)
        bond_type: u8,             // 0:GENESIS, 1:DERIVED, 2:CITES, 3:CONTRADICTS, 4:CORROBORATES
        source_url: String,        // 原始出處
        author: address,           // 提交者
        timestamp_ms: u64,         // 上鏈時間
        purity_score: u64,         // 初始純度 (預設 100)
    }

    // --- 造糖入口函數 (Entry Function) ---
    public fun mint_grain(
        content: String,
        parent_ids: vector<ID>, // 指向上一層糖粒的 ID 列表
        bond_type: u8,
        source_url: String,
        clock: &Clock,          // 系統時鐘，需由前端傳入系統物件 0x6
        ctx: &mut TxContext
    ) {
        // 1. 驗證 bond_type 是否合法 (0-4)
        assert!(bond_type <= 4, EInvalidBondType);

        let id = object::new(ctx);
        let grain_id = object::uid_to_inner(&id);
        let sender = tx_context::sender(ctx);

        // 2. 建立糖粒物件
        let grain = SugarGrain {
            id,
            content,
            parents: parent_ids, // 这里需要 copy 嗎？ vector<ID> 預設可 copy
            bond_type,
            source_url,
            author: sender,
            timestamp_ms: clock::timestamp_ms(clock),
            purity_score: 100,
        };

        // 3. 發出事件 (讓 Indexer 捕捉到圖譜變化)
        event::emit(GrainMinted {
            grain_id,
            parents: parent_ids, // vector 在 Move 中如果元素可 copy，則 vector 可 copy
            bond_type,
            author: sender,
        });

        // 4. 共享物件 (使其成為公共真理檔案，任何人可讀)
        transfer::share_object(grain);
    }
}