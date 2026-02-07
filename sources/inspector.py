# sources/inspector.py
import sys
import os
import requests
import json
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from chain_pusher import push_grain_to_chain
from pysui import SuiConfig, SyncClient

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
sui_client = SyncClient(SuiConfig.default_config())

def fetch_clean_text(url):
    print(f"🕵️ 正在讀取網頁: {url}")
    # 1. 嘗試 Jina Reader
    jina_url = f"https://r.jina.ai/{url}"
    try:
        resp = requests.get(jina_url, timeout=15)
        if resp.status_code == 200: return resp.text
    except: pass

    # 2. 備用方案
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=10)
        soup = BeautifulSoup(resp.text, 'html.parser')
        return soup.get_text()[:10000]
    except Exception as e:
        print(f"❌ 讀取失敗: {e}")
        return None

def analyze_discourse_genealogy(text):
    print("🧠 AI 正在分析言論族譜 (L1-L4)...")
    system_prompt = """
    你是一個言論族譜分析師。請將內容拆解為 JSON:
    {
      "entities": [
        {
          "name": "實體 (如: 比特幣)",
          "stances": [
            {
              "name": "立場 (如: 看多)",
              "claims": [
                {"content": "具體論點", "bond_type": 1}
              ]
            }
          ]
        }
      ]
    }
    規則: 若論點是在反駁，bond_type 設為 3。
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": text[:8000]}],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except: return {}

def get_or_mint_entity(name, url):
    memory_file = "local_memory.json"
    memory = []
    if os.path.exists(memory_file):
        with open(memory_file, "r") as f:
            try: memory = json.load(f)
            except: pass
    
    for item in memory:
        if name.lower() in item['content'].lower(): return item['id']
    
    print(f"🌱 鑄造新實體: {name}")
    new_id = push_grain_to_chain(sui_client, name, [], 0, url)
    if new_id:
        memory.append({"id": new_id, "content": name})
        with open(memory_file, "w") as f: json.dump(memory, f, ensure_ascii=False)
    return new_id

def main():
    if len(sys.argv) < 2: return
    url = sys.argv[1]
    text = fetch_clean_text(url)
    if not text: return
    
    data = analyze_discourse_genealogy(text)
    
    for ent in data.get('entities', []):
        l1_id = get_or_mint_entity(ent['name'], url)
        if not l1_id: continue
        
        for st in ent.get('stances', []):
            print(f"🔹 立場: {st['name']}")
            l2_id = push_grain_to_chain(sui_client, f"{ent['name']}: {st['name']}", [l1_id], 1, url)
            if not l2_id: continue
            
            for cl in st.get('claims', []):
                print(f"🌿 論點: {cl['content'][:15]}...")
                l3_id = push_grain_to_chain(sui_client, cl['content'], [l2_id], cl['bond_type'], url)
                if l3_id:
                    push_grain_to_chain(sui_client, f"Source: {url.split('/')[-1]}", [l3_id], 1, url)

if __name__ == "__main__":
    main()