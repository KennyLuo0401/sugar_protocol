# sources/chain_pusher.py
import sys
from pysui import SuiConfig, SyncClient
from pysui.sui.sui_txn import SyncTransaction

# 引入正確的型別
from pysui.sui.sui_types.address import SuiAddress
from pysui.sui.sui_types.collections import SuiArray
from pysui.sui.sui_types.scalars import ObjectID, SuiString, SuiU8

# ==========================================
# 🔴 請確認 Package ID 與 App.jsx 一致
# ==========================================
PACKAGE_ID = "0x3a89bbef10712247d2ef6bdf70ea9ea3c500182d060c6d507a0cfaf467cead75"
MODULE_NAME = "core"
FUNCTION_NAME = "mint_grain"

def push_grain_to_chain(client, content, parent_ids, bond_type, source_url):
    # 簡單的 Log
    # print(f"   ☁️ 上鏈中... (Parents: {len(parent_ids)})")
    
    tx = SyncTransaction(client=client)
    
    # 1. 轉換 ID: 字串 -> SuiAddress
    converted_parents = [SuiAddress(pid) for pid in parent_ids]
    
    # 2. 封裝陣列: List -> SuiArray (這是 pysui 的規矩)
    vector_parents = SuiArray(converted_parents)
    
    arguments = [
        SuiString(content),
        vector_parents,
        SuiU8(bond_type),
        SuiString(source_url),
        ObjectID("0x6") # Clock Object
    ]
    
    tx.move_call(
        target=f"{PACKAGE_ID}::{MODULE_NAME}::{FUNCTION_NAME}",
        arguments=arguments
    )
    
    result = tx.execute() 
    
    if result.is_ok():
        new_id = None
        if hasattr(result.result_data, 'object_changes'):
            for change in result.result_data.object_changes:
                if change['type'] == 'created':
                    new_id = change['objectId']
                    break
        return new_id 
    else:
        print(f"❌ 交易失敗: {result.result_string}")
        return None