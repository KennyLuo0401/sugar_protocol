# agent.py (安全升級版)
import json
import os
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv  # <--- 新增這行

# 引入上鏈工具
from chain_pusher import push_grain_to_chain, PACKAGE_ID
from pysui import SuiConfig, SyncClient

# ==========================================
# 🔑 設定區 (自動讀取 .env)
# ==========================================
# 1. 載入環境變數
load_dotenv()

# 2. 獲取 Key (如果沒抓到會報錯提醒)
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ 找不到 API Key！請確認你有建立 .env 檔案並填入 OPENAI_API_KEY")

# 3. 設定 OpenAI (新版 SDK 會自動讀取環境變數，但明確指定更保險)
client = OpenAI(api_key=api_key)

# ==========================================
# 👁️ 眼睛：爬蟲模組
# ==========================================
def fetch_latest_news():
    print(f"🕵️ 正在偵察: {TARGET_URL} ...")
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(TARGET_URL, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        articles = soup.select('.loop-card__title-link')
        
        if not articles:
            print("⚠️ 找不到文章，改用測試數據。")
            return "台積電宣佈在高雄擴建第三廠，預計2026量產。", "https://example.com/tsmc"

        latest_article = articles[0]
        title = latest_article.get_text(strip=True)
        link = latest_article.get('href')
        
        print(f"📄 發現最新新聞: {title}")
        print(f"🔗 連結: {link}")
        
        return title, link
        
    except Exception as e:
        print(f"爬蟲錯誤: {e}")
        return None, None

# ==========================================
# 🧠 大腦：提煉模組 (Crystallizer)
# ==========================================
def crystallize_to_grains(text, url):
    print("🧪 AI 正在提煉原子宣稱 (使用 GPT-4o-mini)...")
    
    system_prompt = """
    你是一個資訊原子化引擎。請將輸入的新聞標題或摘要，拆解為 1-3 個獨立的「原子宣稱」。
    輸出格式必須是純粹的 JSON Array，不要 Markdown 標記。
    格式範例:
    [
        {"content": "台積電擴建高雄廠", "bond_type": 0},
        {"content": "預計2026年量產", "bond_type": 1}
    ]
    bond_type 定義: 0=GENESIS(新事實), 1=DERIVED(延伸細節), 3=CONTRADICTS(反駁)
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text}
        ],
        temperature=0.2
    )

    raw_content = response.choices[0].message.content
    clean_json = raw_content.replace("```json", "").replace("```", "").strip()
    
    return json.loads(clean_json)

# ==========================================
# 🤖 主程序
# ==========================================
def run_agent():
    # 初始化 Sui
    cfg = SuiConfig.default_config()
    sui_client = SyncClient(cfg) # 變數改名避免跟 openai client 混淆
    print(f"👤 Agent 錢包: {cfg.active_address}")

    # 抓新聞
    news_text, news_url = fetch_latest_news()
    if not news_text:
        return

    # AI 拆解
    try:
        grains = crystallize_to_grains(news_text, news_url)
        print(f"💎 提煉出 {len(grains)} 顆糖粒，準備上鏈...")
        
        for grain in grains:
            push_grain_to_chain(
                client=sui_client,
                content=grain['content'],
                parent_ids=[], 
                bond_type=grain['bond_type'],
                source_url=news_url
            )
            
    except Exception as e:
        print(f"❌ 處理失敗: {e}")

if __name__ == "__main__":
    run_agent()