#驗證code(版本1)
import pandas as pd
import datetime
# 此檔案需要手動調整要驗證的股票代號

# 讀取股價數據
price_data = pd.read_csv('price_3687.csv', index_col='Date', parse_dates=True)

# 讀取輸出數據
csv_file = 'output_3687.csv'
data = pd.read_csv(csv_file)

def get_historical_prices(stock_symbol, start_date, end_date):
    # 篩選日期範圍內的價格數據
    filtered_data = price_data.loc[start_date:end_date, stock_symbol]
    return filtered_data

# 檢查字串是否可以轉換為浮點數
def is_float(value):
    try:
        float(value)
        return True
    except ValueError:
        return False

# 開始寫入結果到文件
with open('3687_results.txt', 'w', encoding='utf-8') as result_file:

    # 讀取每一行數據，進行驗證
    for index, row in data.iterrows():
        stock_symbol = '3687.TW'
        
        if pd.isna(row['Recommended holding period']):
            result_file.write(f"Skipping entry {index} due to missing holding period.\n")
            continue

        holding_period_str = row['Recommended holding period']
        bullish_bearish = row['Bullish/Bearish']
        if 'months' in holding_period_str:
            
            # 格式問題處理  Extract the first number before hyphen (if present)
            # 提取持有期的數字部分
            holding_period = int(holding_period_str.split()[0].split('-')[0])
            result_file.write(f"持有時間 : {holding_period} 個月\n")
        else:
            result_file.write(f"Skipping entry {index} due to invalid holding period format: {holding_period_str}\n")
            continue

        start_date = pd.Timestamp('2023-01-03')
        end_date = start_date + pd.DateOffset(months=holding_period)

        historical_prices = get_historical_prices(stock_symbol, start_date, end_date)

        # 驗證是否達到停利 (是否達到推薦賣出的價格)
        reached_take_profit = False
        if pd.notna(row['Recommended selling price']) and is_float(row['Recommended selling price'].split()[0]):
            recommended_selling_price = float(row['Recommended selling price'].split()[0])
            for date, price in historical_prices.items():
                if price >= recommended_selling_price:
                    reached_take_profit = True
                    #time = date
                    #print(time)
                    break

        # 超過持有時間後的效益
        final_price = historical_prices.iloc[-1]
        initial_price = float(row['Recommended buying price'].split()[0]) if pd.notna(row['Recommended buying price']) and is_float(row['Recommended buying price'].split()[0]) else None
        
        # 持有期結束時的股票價格 - 推薦買入價格 (獲利) 
        profit_or_loss = final_price - initial_price if initial_price is not None else None
        
        # 寫到TXT
        result_file.write(f"第 {index+1} 筆驗證資料:\n")
        result_file.write(f"看漲或看跌 : {bullish_bearish} \n")
        result_file.write(f"start_date : {start_date}\n")
        result_file.write(f"end_date : {end_date}\n")
        result_file.write(f"是否達到停利: {reached_take_profit}\n")
        result_file.write(f"initial_price : {initial_price}\n")
        result_file.write(f"final_price : {final_price}\n")
        result_file.write(f"Profit or Loss after holding period: {profit_or_loss if profit_or_loss is not None else 'N/A'}\n")
        
        # 看漲 -> 達到停利  OR 獲利大於 0 -> CORRECT，否則INCORRECT
        # 看跌 -> 達到停利  OR 獲利大於 0 -> INCORRECT，否則CORRECT
        if bullish_bearish == 'Bullish' :
            if reached_take_profit or (profit_or_loss is not None and profit_or_loss > 0):
                result_file.write("=> CORRECT!\n")
            else:
                result_file.write("=> INCORRECT!\n")
        else: #Bearish
            if reached_take_profit or (profit_or_loss is not None and profit_or_loss > 0):
                result_file.write("=> INCORRECT!\n")
            else:
                result_file.write("=> CORRECT!\n")
            
        result_file.write("==============================\n")
