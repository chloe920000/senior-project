import yfinance as yf
import pandas as pd

date = '2010-01-01'
stocks = ['2330.TW', '3443.TW', '2002.TW']

# Create an empty DataFrame to store stock data
all_stock_data = pd.DataFrame()

for stock_no in stocks:
    stock = yf.Ticker(stock_no)
    stock_data = stock.history(start=date)
    stock_data = stock_data[['Close']]  # Selecting only the 'Close' column
    stock_data.rename(columns={'Close': stock_no}, inplace=True)  # Renaming the column to the stock number
    
    # Combine the data
    if all_stock_data.empty:
        all_stock_data = stock_data
    else:
        all_stock_data = all_stock_data.join(stock_data, how='outer')

# Remove timezone information from the datetime index
all_stock_data.index = all_stock_data.index.tz_localize(None)

# 寫入 Excel 檔案
all_stock_data.to_excel('daily_price.xlsx')
