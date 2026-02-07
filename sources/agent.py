# sources/agent.py (L1-L4 族譜同步版)
import json
import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
from chain_pusher import push_grain_to_chain
from pysui import SuiConfig, SyncClient

# 1. 初始化設定
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
sui_client = SyncClient(SuiConfig.default_config())
TARGET_URL = "https://abmedia.io" # 你可以隨時換成別的新聞網

# 2. 爬蟲模組
def fetch_latest_news():
    print(f"🕵️ 正在偵察: {TARGET_URL} ...")
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(TARGET_URL, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 針對 ABMedia 的選擇器
        articles = soup.select('.loop-card__title-link')
        if not articles:
            print("⚠️ 找不到文章，使用測試數據。")
            return "MicroStrategy 再次購買比特幣，市場情緒高昂。", "https://example.com/btc"

        latest = articles[0]
        title = latest.get_text(strip=True)
        link = latest.get('href')
        print(f"📄 鎖定新聞: {title}")
        return title, link
    except Exception as e:
        print(f"❌ 爬蟲失敗: {e}")
        return None, None

# 3. 核心升級：L1-L4 族譜分析 Prompt
def analyze_genealogy(text):
    print("🧠 AI 正在進行族譜結構化分析 (Entity -> Stance -> Claim)...")
    
    # 🔴 這裡就是你要修改的關鍵 Prompt！
    system_prompt = """
    你是一個言論族譜分析師。請將新聞內容拆解為「階層化」的 JSON 結構：

    目標結構 (L1 -> L2 -> L3):
    {
      "entities": [
        {
          "name": "L1 實體 (如: Bitcoin, Elon Musk)",
          "stances": [
            {
              "name": "L2 立場 (如: Bullish, Skeptical, Regulatory Pressure)",
              "claims": [
                {
                  "content": "L3 具體論點或新聞事實",
                  "bond_type": 1 
                }
              ]
            }
          ]
        }
      ]
    }

    bond_type 規則:
    - 1 (綠色): 支持、延伸、事實陳述。
    - 3 (紅色): 反駁、衝突、對立觀點。
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"❌ AI 分析失敗: {e}")
        return {}

# 4. 記憶與遞迴上鏈模組
def get_or_mint_entity(name, url):
    # 簡單的本地記憶，避免重複鑄造同一個實體
    memory_file = "local_memory.json"
    memory = []
    if os.path.exists(memory_file):
        with open(memory_file, "r") as f:
            try: memory = json.load(f)
            except: pass
    
    # 檢查是否已存在
    for item in memory:
        if name.lower() in item['content'].lower(): 
            return item['id']

    # 不存在則鑄造
    print(f"🌱 鑄造新 L1 實體: {name}")
    new_id = push_grain_to_chain(sui_client, name, [], 0, url)
    if new_id:
        memory.append({"id": new_id, "content": name})
        with open(memory_file, "w") as f: json.dump(memory, f, ensure_ascii=False)
    return new_id

def run_agent():
    print(f"👤 Agent Address: {SuiConfig.default_config().active_address}")
    
    # 1. 抓新聞
    text, url = fetch_latest_news()
    if not text: return

    # 2. AI 分析 (新版)
    data = analyze_genealogy(text)
    
    # 3. 遞迴上鏈 (從 Entity -> Stance -> Claim)
    if 'entities' not in data:
        print("⚠️ AI 沒有回傳正確結構")
        return

    for ent in data['entities']:
        # L1: 實體
        l1_id = get_or_mint_entity(ent['name'], url)
        if not l1_id: continue
        
        for st in ent.get('stances', []):
            # L2: 立場 (父節點是 L1)
            print(f"  🔹 L2 立場: {st['name']}")
            l2_id = push_grain_to_chain(sui_client, f"{ent['name']}: {st['name']}", [l1_id], 1, url)
            
            if not l2_id: continue

            for cl in st.get('claims', []):
                # L3: 論點 (父節點是 L2)
                print(f"    🌿 L3 論點: {cl['content'][:20]}...")
                push_grain_to_chain(sui_client, cl['content'], [l2_id], cl['bond_type'], url)

if __name__ == "__main__":
    run_agent()