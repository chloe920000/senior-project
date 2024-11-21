import asyncio
from datetime import datetime, timedelta
from supabase import create_client, Client
from together import Together

import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

# Supabase client configuration
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Together API client
together_client = Together(api_key=os.environ.get("TOGETHER_API_KEY"))


async def together_response(news, question):
    """
    使用 Together API 生成回應

    :param news: string 新聞內容
    :param question: string 問題指令
    :return: string AI 回應
    """

    messages = [
        {
            "role": "system",
            "content": (
                "以下是今天的新聞資訊。請根據這些資訊判斷一周內賣出是否可能獲利。請按照以下格式回答：\n\n"
                "1. 如果預測可以獲利，請回答：#好\n"
                "2. 如果預測不會獲利，請回答：#不好\n"
                "3. 如果資訊與股市無關，請回答：#無關\n\n"
                "請詳述您的理由，請用**理由**作為回答格式。\n"
            ),
        },
        {
            "role": "user",
            "content": f"問題:\n{question}\n\n文章:\n{news}\n\n回答:",
        },
    ]

    try:
        # 呼叫 Together API
        response = together_client.chat.completions.create(
            model="meta-llama/Meta-Llama-3.1-405B-Instruct-Turbo",
            messages=messages,
            max_tokens=512,
            temperature=0.7,
        )
        print("Together Response:", response)
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error with Together API: {e}")
        return "exception"


def response_to_signal(text):
    """
    解析 AI 回應的文字以生成訊號

    :param text: string 回應文字
    :return: int 回應訊號
    """
    if "不好" in text:
        return -1
    elif "好" in text:
        return 1
    elif "無關" in text:
        return 0
    else:
        return None  # 處理未知情況


async def chat(date, stocks):
    """
    從 Together API 獲取新聞訊號並更新 Supabase

    :param date: string 日期
    :param stocks: list 股票列表
    """
    end_date = datetime.strptime(date, "%Y-%m-%d")
    start_date = end_date - timedelta(days=30)

    results = []

    for stock in stocks:
        stock_id = stock.get("stock_id")
        stock_name = stock.get("stock_name")
        query = f"請找出對{stock_id}{stock_name}股票的建議投資策略有影響的新聞資料"
        signals = []

        # 從 Supabase 中提取數據
        response = (
            supabase.from_("news_content").select("*").eq("stockID", stock_id).execute()
        )
        news_data = response.data

        if not news_data:
            print(f"No news found for stockID: {stock_id}")
            continue

        for news in news_data:
            date_obj = news["date"]

            # 確保 date_obj 是 date 型別
            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d").date()

            if start_date.date() <= date_obj <= end_date.date():
                print(f"Stock&News: {stock_name}, Date: {date_obj}")

                ans = await together_response(news["content"], query)
                print(ans)
                sig = response_to_signal(ans)

                if sig is None:
                    continue  # 跳過未知情況

                if sig == 0:
                    # 刪除該筆資料
                    supabase.from_("news_content").delete().eq(
                        "id",
                        news["id"],
                    ).execute()
                    print("Deleted #無關 資料")
                else:
                    signals.append([stock_name, news["id"], sig])
                    result = f"Stock&News: {stock_name}\nDate: {date_obj}\nSignal: {sig}\nAnswer: {ans}\n"
                    results.append(result)
        print("無關新聞過濾完成。")


def get_together_response(date, stocks):
    asyncio.run(chat(date, stocks))


"""
# 示例日期
test_date = "2024-11-01"

# 示例股票数据
test_stocks = [
    {"stock_id": "2002", "stock_name": "中鋼"},
    {"stock_id": "1504", "stock_name": "東元"},
]

# 调用测试函数
get_together_response(test_date, test_stocks)
"""
