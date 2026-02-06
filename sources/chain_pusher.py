# chain_pusher.py (路徑修正版)
import sys
from pysui import SuiConfig, SyncClient
from pysui.sui.sui_txn import SyncTransaction

# 🔴 修正 1: SuiAddress 必須從 address 模組引入，不能從 scalars 引入
from pysui.sui.sui_types.address import SuiAddress
# 🔴 修正 2: 引入集合類型 SuiArray
from pysui.sui.sui_types.collections import SuiArray
# 🔴 修正 3: 純量類型
from pysui.sui.sui_types.scalars import ObjectID, SuiString, SuiU8

# ==========================================
# 🔴 請確認 Package ID 正確
# ==========================================
PACKAGE_ID = "0x3a89bbef10712247d2ef6bdf70ea9ea3c500182d060c6d507a0cfaf467cead75"
MODULE_NAME = "core"
FUNCTION_NAME = "mint_grain"

def push_grain_to_chain(client, content, parent_ids, bond_type, source_url):
    print(f"🚀 上鏈中: {content[:10]}... (Parents: {len(parent_ids)})")
    
    tx = SyncTransaction(client=client)
    
    # ----------------------------------------------------
    # 🔧 資料轉換區
    # ----------------------------------------------------
    # 1. 將字串 ID 轉為 SuiAddress (因為 Move vector<ID> 底層是 address)
    # pysui 要求陣列裡的元素必須是明確的型別
    converted_parents = [SuiAddress(pid) for pid in parent_ids]
    
    # 2. 用 SuiArray 包裝 (這是 pysui 對應 Move vector 的方式)
    vector_parents = SuiArray(converted_parents)
    
    arguments = [
        SuiString(content),
        vector_parents,     # <--- 這裡傳入 SuiArray([SuiAddress, ...])
        SuiU8(bond_type),
        SuiString(source_url),
        ObjectID("0x6")     # Clock 物件
    ]
    
    tx.move_call(
        target=f"{PACKAGE_ID}::{MODULE_NAME}::{FUNCTION_NAME}",
        arguments=arguments
    )
    
    # 執行交易
    result = tx.execute() 
    
    if result.is_ok():
        new_id = None
        if hasattr(result.result_data, 'object_changes'):
            for change in result.result_data.object_changes:
                if change['type'] == 'created':
                    new_id = change['objectId']
                    break
        
        digest = getattr(result.result_data, 'digest', 'unknown')
        print(f"✅ 成功! ID: {new_id} | Tx: https://suiscan.xyz/testnet/tx/{digest}")
        return new_id 
    else:
        print(f"❌ 失敗: {result.result_string}")
        return None