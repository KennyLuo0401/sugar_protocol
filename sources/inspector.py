# inspector.py (具備記憶功能的升級版)
import sys
import os
import requests
import json
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from chain_pusher import push_grain_to_chain, PACKAGE_ID, MODULE_NAME
from pysui import SuiConfig, SyncClient

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 初始化 Sui
sui_cfg = SuiConfig.default_config()
sui_client = SyncClient(sui_cfg)

# ... (fetch_clean_text 函數保持不變，請保留之前的代碼) ...
def fetch_clean_text(url):
    # (請保留你原本寫好的 fetch_clean_text 邏輯)
    print(f"🕵️ 正在讀取網頁: {url}")
    # ... 省略以節省篇幅 ...
    # 這裡為了演示，假設你已經有上面的 fetch_clean_text 代碼
    jina_url = f"https://r.jina.ai/{url}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(jina_url, headers=headers)
        if response.status_code == 200: return response.text
    except: pass
    return "無法讀取內容，請檢查網址。"

# ... (analyze_logic_tree 函數保持不變) ...
def analyze_logic_tree(text):
    # (請保留原本的邏輯)
    print("🧠 AI 正在進行邏輯拓撲分析...")
    system_prompt = """
    你是一個邏輯拓撲分析師。請分析這篇文章，拆解出：
    1. 一個「核心議題 (Main Issue)」(作為根節點)
    2. 數個「關鍵論點 (Arguments)」(作為子節點)
    輸出 JSON:
    {
        "root": { "content": "核心議題描述", "bond_type": 0 },
        "children": [ { "content": "論點...", "bond_type": 1 } ]
    }
    """
    truncated_text = text[:8000]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": truncated_text}],
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    return json.loads(response.choices[0].message.content)

# ==========================================
# 🔍 修改後的函數：寬鬆連結版 (Loose Bonding)
# ==========================================
def find_existing_topic(new_topic_content):
    print("📡 正在掃描鏈上既有議題 (Memory Scan)...")
    
    memory_file = "local_memory.json"
    existing_roots = []
    
    if os.path.exists(memory_file):
        with open(memory_file, "r") as f:
            try:
                existing_roots = json.load(f)
            except:
                existing_roots = []
            
    if not existing_roots:
        return None

    # 顯示目前記憶中有哪些話題
    print(f"🧠 記憶庫中有 {len(existing_roots)} 個議題，正在進行模糊比對...")
    
    candidates_str = json.dumps(existing_roots, ensure_ascii=False)
    
    # 🔴 關鍵修改：放寬判定標準 Prompt
    check_prompt = f"""
    我有一個新議題："{new_topic_content}"。
    以下是資料庫已有的議題列表：
    {candidates_str}
    
    任務：請判斷新議題是否屬於列表中某個議題的「子集合」、「相關事件」、「後續發展」或「同一領域」？
    
    判定規則：
    1. 只要有高度相關性（例如都提到 '比特幣'、'xAI'、'馬斯克'），就視為同一類。
    2. 不要太嚴格，我們希望把相關的議題聚合在一起。
    
    若找到相關議題，請只回傳該議題的 ID (例如 "0x123...")。
    若完全不相關，請回傳 "NONE"。
    """
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": check_prompt}],
            temperature=0.1 # 溫度低，確保回答穩定
        )
        
        result = response.choices[0].message.content.strip()
        
        if "0x" in result and result != "NONE":
            # 清理 ID (移除可能存在的引號)
            clean_id = result.replace('"', '').replace("'", "").strip()
            print(f"🔗 成功找到關聯！將合併至舊議題: {clean_id}")
            return clean_id
        else:
            print("✨ 判定為全新議題。")
            return None
            
    except Exception as e:
        print(f"⚠️ 比對過程發生錯誤: {e}")
        return None

def save_root_to_memory(content, grain_id):
    """將新的 Root 存入本地記憶，供下次比對"""
    memory_file = "local_memory.json"
    data = []
    if os.path.exists(memory_file):
        with open(memory_file, "r") as f:
            data = json.load(f)
    
    # 加入新紀錄 (只保留最近 20 筆以免 Token 爆炸)
    data.append({"id": grain_id, "content": content})
    if len(data) > 20: 
        data = data[-20:]
        
    with open(memory_file, "w") as f:
        json.dump(data, f, ensure_ascii=False)

# ==========================================
# 主程式
# ==========================================
def main():
    if len(sys.argv) < 2:
        print("使用方式: python inspector.py <URL>")
        return
    
    target_url = sys.argv[1]
    clean_text = fetch_clean_text(target_url)
    if not clean_text: return

    # 1. 分析
    logic_tree = analyze_logic_tree(clean_text)
    root_content = logic_tree['root']['content']
    
    # 2. 關鍵修改：先檢查是否存在
    existing_id = find_existing_topic(root_content)
    
    root_id = None
    
    if existing_id:
        # 如果找到了舊的議題，我們就不用鑄造新的 Root
        # 直接把舊的 ID 當作這次的 "Root ID"
        root_id = existing_id
        print(f"🔄 跳過 Root 鑄造，直接掛載於現有節點: {root_id}")
    else:
        # 沒找到，鑄造新的
        print(f"🌱 正在鑄造核心議題: {root_content}")
        root_id = push_grain_to_chain(
            client=sui_client,
            content=root_content,
            parent_ids=[], 
            bond_type=0,   
            source_url=target_url
        )
        # 存入記憶
        if root_id:
            save_root_to_memory(root_content, root_id)

    if not root_id:
        print("❌ 無法取得 Root ID，終止。")
        return

    # 3. 鑄造子節點 (這些是新的論點，無論 Root 是新是舊，這些都要上鏈)
    children = logic_tree.get('children', [])
    print(f"🌿 正在鑄造 {len(children)} 個衍生論點...")

    for child in children:
        push_grain_to_chain(
            client=sui_client,
            content=child['content'],
            parent_ids=[root_id], # 這裡會指向 (新 Root) 或 (舊 Root)
            bond_type=child['bond_type'],
            source_url=target_url
        )

if __name__ == "__main__":
    main()