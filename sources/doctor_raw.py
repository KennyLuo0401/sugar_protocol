import requests
import json

# ==========================================
# 🔴 請確認這裡跟你的 App.jsx 一樣
# ==========================================
PACKAGE_ID = "0x3a89bbef10712247d2ef6bdf70ea9ea3c500182d060c6d507a0cfaf467cead75" 
MODULE_NAME = "core"
EVENT_NAME = "GrainMinted"
RPC_URL = "https://fullnode.testnet.sui.io:443"

def rpc_call(method, params):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": method,
        "params": params
    }
    response = requests.post(RPC_URL, json=payload)
    return response.json()

def diagnose():
    print(f"🏥 正在診斷鏈上數據 (直接連線 RPC)...")
    
    # 1. 查詢事件
    query_payload = {
        "MoveEventType": f"{PACKAGE_ID}::{MODULE_NAME}::{EVENT_NAME}"
    }
    
    print("📡 正在掃描 GrainMinted 事件...")
    res = rpc_call("suix_queryEvents", [query_payload, None, 50, True]) # query, cursor, limit, descending
    
    if "error" in res:
        print(f"❌ RPC 錯誤: {res['error']}")
        return

    events = res.get("result", {}).get("data", [])
    print(f"📊 掃描到 {len(events)} 筆最近的 Grain 事件")
    
    if not events:
        print("❌ 鏈上沒有任何數據！")
        return

    # 收集 ID
    grain_ids = []
    for e in events:
        if 'parsedJson' in e:
            grain_ids.append(e['parsedJson']['grain_id'])
            
    # 2. 批量讀取物件
    print(f"🔍 正在讀取 {len(grain_ids)} 個物件的詳細內容...")
    
    # Sui 的 multiGetObjects 參數格式
    obj_res = rpc_call("sui_multiGetObjects", [
        grain_ids, 
        {
            "showContent": True,
            "showType": True
        }
    ])
    
    objects = obj_res.get("result", [])
    
    roots = 0
    children = 0
    orphans = 0

    print("\n--- 詳細檢測 ---")
    for obj in objects:
        if "data" in obj and "content" in obj["data"]:
            fields = obj["data"]["content"]["fields"]
            obj_id = obj["data"]["objectId"]
            
            # 取得關鍵欄位
            bond_type = fields.get("bond_type")
            content_text = fields.get("content", "")[:20]
            
            # 🛡️ 雙重檢查 parents
            parents = fields.get("parents", []) or fields.get("parent_ids", [])
            
            status = ""
            if bond_type == 0:
                roots += 1
                status = "🟠 ROOT (正常)"
            else:
                children += 1
                if len(parents) > 0:
                    status = f"🟢 CHILD -> 父: {parents[0][:6]}... (正常)"
                else:
                    orphans += 1
                    status = "❌ 孤兒 (異常! 缺父母)"
            
            print(f"ID: {obj_id[:6]}... | Type: {bond_type} | Parents: {len(parents)} | {status}")

    print("\n" + "="*30)
    print("🩺 最終診斷報告")
    print("="*30)
    print(f"總檢查節點: {len(grain_ids)}")
    print(f"🟠 核心議題 (Roots): {roots}")
    print(f"🟢 成功連線子節點: {children - orphans}")
    print(f"❌ 失敗孤兒子節點: {orphans}")
    print("="*30)

    if orphans > 0:
        print("\n🔥 結論：【兇手是 chain_pusher.py】")
        print("你的上鏈程式沒有成功把 parent_id 寫入區塊鏈，導致子節點變成孤兒。")
    elif children == 0:
         print("\n🧊 結論：你的腳本只生了 Root，完全沒生小孩。")
    else:
        print("\n✅ 結論：鏈上數據完全健康！那問題就在前端顯示。")

if __name__ == "__main__":
    diagnose()