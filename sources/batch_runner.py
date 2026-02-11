# batch_runner.py
import subprocess
import time
import os

# 你的目標網址清單
urls = [
    "https://abmedia.io/bitcoin-etf-outflow-and-inflow",
    "https://abmedia.io/bitcoin-etf-outflow-and-inflow",
    "https://abmedia.io/ark-cathie-wood-nancy-pelosi-stocks-2026",
    "https://abmedia.io/elon-musk-xai-tesla-spacex-expand-ai-supply-chain",
    "https://abmedia.io/what-happens-to-minnesota",
    "https://abmedia.io/tether-invests-anchorage-digital-bank",
    "https://abmedia.io/the-commodities-trade-becomes-the-new-investment",
    "https://abmedia.io/gemini-to-exit-u-k-eu-and-australia-reduce-staff-by-25-and-focus-on-u-s-and-prediction-markets",
    "https://abmedia.io/30-days-of-main-coins",
    "https://abmedia.io/pentagon-probe-spacex-alleged-chinese-investment",
]

def run_batch():
    # 1. 為了效果最好，建議先清空記憶 (可選)
    if os.path.exists("local_memory.json"):
        os.remove("local_memory.json")
        print("🧹 已清空舊記憶，開始建立全新星系...")

    print(f"📦 準備處理 {len(urls)} 篇文章...")
    print("-" * 30)

    for i, url in enumerate(urls):
        print(f"\n[第 {i+1}/{len(urls)} 篇] 正在派 Agent 前往: {url.split('/')[-1]} ...")
        
        # 呼叫 inspector.py
        try:
            subprocess.run(["python", "inspector.py", url], check=False)
        except Exception as e:
            print(f"❌ 執行錯誤: {e}")

        # 休息一下，避免被 ABMedia 的防火牆擋住 (429 Too Many Requests)
        print("☕️ 休息 1 秒鐘...")
        time.sleep(1)

    print("\n" + "="*30)
    print("🎉 全部分析完成！請打開前端網頁查看星系聚合結果。")

if __name__ == "__main__":
    run_batch()