import os
import pandas as pd
from supabase import create_client, Client
import datetime
import re  

# 初始化 supabase
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

def get_historical_prices(stock_symbol, start_date, end_date):
    # 從 supabase 抓 adj_price (調整後股價)
    response = supabase.table('daily_price').select('date, adj_price').eq('stockID', stock_symbol).gte('date', start_date).lte('date', end_date).execute()
    
    if response.data:
        df = pd.DataFrame(response.data)
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df['adj_price']
    else:
        return pd.Series(dtype='float64')  

def is_float(value):
    try:
        float(value.replace(',', ''))  # 移除逗號來處理數字格式
        return True
    except ValueError:
        return False

# analyze result 的 路徑
analyze_result_path = 'C://Users//Chloe//OneDrive//桌面//senior_project//llama_analyze//analyze result'

for stock_dir in os.listdir(analyze_result_path):
    stock_symbol = stock_dir  
    print(stock_symbol)
    stock_folder_path = os.path.join(analyze_result_path, stock_dir)
    
    csv_file = os.path.join(stock_folder_path, f'output_{stock_symbol}.csv')
    data = pd.read_csv(csv_file)
    
    result_file_path = os.path.join(stock_folder_path, f'{stock_symbol}_results.txt')
    
    with open(result_file_path, 'w', encoding='utf-8') as result_file:
        for index, row in data.iterrows():
            if pd.isna(row['Recommended holding period']):
                result_file.write(f"Skipping entry {index} due to missing holding period.\n")
                continue

            holding_period_str = row['Recommended holding period']
            bullish_bearish = row['Bullish/Bearish']
            if 'month' in holding_period_str:
                holding_period_str_cleaned = re.sub(r'\[|\]', '', holding_period_str)  # 移除方括号
                holding_period = int(holding_period_str_cleaned.split()[0].split('-')[0])
                result_file.write(f"持有時間 : {holding_period} 個月\n")
            else:
                result_file.write(f"Skipping entry {index} due to invalid holding period format: {holding_period_str}\n")
                continue

            start_date = pd.Timestamp(row['Date'])  # 使用 CSV 中的日期作为开始日期
            print("start : ",start_date)
            end_date = start_date + pd.DateOffset(months=holding_period)
            print("end : ",end_date)
            historical_prices = get_historical_prices(stock_symbol, start_date, end_date)

            reached_take_profit = False
            if pd.notna(row['Recommended selling price']) and is_float(row['Recommended selling price'].replace('NTD', '').strip()):
                recommended_selling_price = float(row['Recommended selling price'].replace('NTD', '').replace(',', '').strip())
                for date, price in historical_prices.items():
                    if price >= recommended_selling_price:
                        reached_take_profit = True
                        break
            
            final_price = historical_prices.iloc[-1] if not historical_prices.empty else None
            initial_price = None
            if pd.notna(row['Recommend buy or not']) and row['Recommend buy or not'] != "No":
                initial_price = float(row['Recommend buy or not'].replace('NTD', '').replace(',', '').strip()) if is_float(row['Recommend buy or not']) else None
            
            profit_or_loss = final_price - initial_price if initial_price is not None and final_price is not None else None

            result_file.write(f"第 {index+1} 筆驗證資料:\n")
            result_file.write(f"看漲或看跌 : {bullish_bearish} \n")
            result_file.write(f"開始日期 : {start_date}\n")
            result_file.write(f"結束日期 : {end_date}\n")
            result_file.write(f"是否達到停利: {reached_take_profit}\n")
            result_file.write(f"初始股價 : {initial_price}\n")
            result_file.write(f"最後股價 : {final_price}\n")
            result_file.write(f"獲利 : {profit_or_loss if profit_or_loss is not None else 'N/A'}\n")
            
            if profit_or_loss is not None and initial_price is not None and initial_price != 0:
                percentage = profit_or_loss / initial_price
                result_file.write(f"Profit or Loss Percentage: {percentage:.2%}\n")
            else:
                result_file.write("Profit or Loss Percentage: N/A\n")
                
            if bullish_bearish.lower() == 'bullish':
                if reached_take_profit or (profit_or_loss is not None and profit_or_loss > 0):
                    result_file.write("=> CORRECT!\n")
                else:
                    result_file.write("=> INCORRECT!\n")
            else:  # Bearish
                if reached_take_profit or (profit_or_loss is not None and profit_or_loss > 0):
                    result_file.write("=> INCORRECT!\n")
                else:
                    result_file.write("=> CORRECT!\n")

            result_file.write("==============================\n")
