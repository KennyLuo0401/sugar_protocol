import os
import json
import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# 載入 API Key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ==========================================
# 🧪 實驗區：在這裡修改你的 Prompt
# ==========================================
# 你可以在這裡調整：
# 1. 你對 AI 的角色設定 (Role)
# 2. 你想要的 JSON 格式 (Format)
# 3. 你對「關鍵字」的定義 (Definition)

SYSTEM_PROMPT = """
你是一個資訊架構師。請分析使用者輸入的新聞文章內容，並提取出結構化資訊。

請回傳一個 JSON 物件，必須包含以下欄位：
1. "root_topic": 一個簡短的字串，代表這篇文章的核心議題（例如：「比特幣價格波動」、「xAI 法律糾紛」）。
2. "keywords": 一個字串陣列 (Array of Strings)，列出文章中出現的最關鍵實體 (人名、公司名、專有名詞)。
3. "summary": 一句簡短的摘要。
4. "arguments": 陣列，包含文章中的主要論點。

JSON 格式範例：
{
    "root_topic": "台積電高雄擴廠",
    "keywords": ["台積電", "高雄", "2nm製程", "魏哲家"],
    "summary": "台積電確認將在高雄增設第三座2nm晶圓廠。",
    "arguments": [
        "高雄廠將導入最先進製程",
        "預計 2026 年量產"
    ]
}
"""

# ==========================================
# 🛠️ 工具區 (直接複製過來，確保環境一致)
# ==========================================
def fetch_text(url):
    print(f"🕵️ 正在讀取: {url} ...")
    # 1. 嘗試 Jina
    try:
        jina_response = requests.get(f"https://r.jina.ai/{url}")
        if jina_response.status_code == 200:
            return jina_response.text
    except:
        pass
    
    # 2. 備用 BeautifulSoup
    try:
        resp = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            soup = BeautifulSoup(resp.text, 'html.parser')
            for script in soup(["script", "style"]): script.extract()
            return soup.get_text()[:10000] # 截斷過長內容
    except Exception as e:
        return f"Error: {e}"
    return None

def test_prompt(url):
    # 1. 抓取文章
    article_text = fetch_text(url)
    if not article_text or len(article_text) < 50:
        print("❌ 讀取失敗或內容太短")
        return

    print("🧠 AI 正在分析 (Testing Prompt)...")
    
    # 2. 發送給 GPT-4o-mini
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": article_text[:8000]} # 避免 Token 爆炸
            ],
            temperature=0.3, # 溫度低一點，結果比較穩定
            response_format={"type": "json_object"}
        )
        
        # 3. 解析並美化輸出
        result = response.choices[0].message.content
        parsed_json = json.loads(result)
        
        print("\n" + "="*40)
        print(f"📰 分析結果 ({url.split('/')[-1]})")
        print("="*40)
        print(json.dumps(parsed_json, indent=4, ensure_ascii=False))
        print("="*40 + "\n")
        
    except Exception as e:
        print(f"❌ API 錯誤: {e}")

# ==========================================
# 🚀 執行區
# ==========================================
# ==========================================
# 🚀 執行區
# ==========================================
if __name__ == "__main__":
    # 1. 定義一個列表 (List)，用中括號 [] 包起來
    # 每一行網址都要用引號 "" 包住，並且用逗號 , 隔開
    target_urls = [
        "https://abmedia.io/bitmine-tom-lee-jack-yi-garret-jin",
        "https://abmedia.io/elon-musk-xai-is-hiring-crypto-finance-experts",
        "https://abmedia.io/galaxy-digital-cryptoquant-bitcoin-price-drawdown-58k",
        "https://abmedia.io/bitmine-7b-paper-loss-eth-trend-reserch",
        "https://abmedia.io/openai-claims-xai-destroyed-evidence",
        "https://abmedia.io/strategy-digital-credit-waived-from-30-percentage-dividend-tax",
        "https://abmedia.io/xai-joins-spacex-to-ipo",
        "https://abmedia.io/market-update-as-of-3rd-feb-2026",
        "https://abmedia.io/is-btc-losing-its-position"
    ]

    # 2. 使用迴圈 (For Loop) 一個一個拿出來測試
    print(f"📦 準備測試 {len(target_urls)} 篇文章...\n")
    
    for url in target_urls:
        test_prompt(url) # 呼叫上面的函數