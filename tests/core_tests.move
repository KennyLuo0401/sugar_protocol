#[test_only]
module sugar_protocol::core_tests {
    use std::string;
    use std::vector;
    use sui::test_scenario::{Self, Scenario};
    use sui::clock::{Self};
    use sugar_protocol::core::{Self, SugarGrain};

    // 模擬參與者
    const ADMIN: address = @0xA;
    const USER: address = @0xB;

    // 初始化測試場景
    fun init_test_scenario(): Scenario {
        test_scenario::begin(ADMIN)
    }

    #[test]
    fun test_mint_genesis_grain() {
        let scenario = init_test_scenario();
        let ctx = test_scenario::ctx(&mut scenario);

        // 1. 建立並共享一個模擬時鐘
        let clock = clock::create_for_testing(ctx);
        clock::share_for_testing(clock);
        
        // 進入下一個交易 (模擬 USER 操作)
        test_scenario::next_tx(&mut scenario, USER);
        {
            let clock = test_scenario::take_shared<sui::clock::Clock>(&scenario);
            let ctx = test_scenario::ctx(&mut scenario);

            // 2. USER 鑄造一顆 "創世糖粒" (沒有父母)
            let empty_parents = vector::empty<sui::object::ID>();
            
            core::mint_grain(
                string::utf8(b"Bitcoin is a decentralized currency."),
                empty_parents,
                0, // GENESIS
                string::utf8(b"https://whitepaper.io"),
                &clock,
                ctx
            );

            test_scenario::return_shared(clock);
        };

        // 進入下一個交易 (驗證結果)
        test_scenario::next_tx(&mut scenario, USER);
        {
            // 3. 檢查系統中是否真的存在這顆糖粒
            // 注意：因為我們用 share_object，所以用 take_shared
            let grain = test_scenario::take_shared<SugarGrain>(&scenario);
            
            // 可以在這裡加更多 assert 來檢查內容...
            
            // 測試結束，歸還物件
            test_scenario::return_shared(grain);
        };

        test_scenario::end(scenario);
    }
}