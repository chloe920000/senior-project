import yfinance as yf
import pandas as pd

date = '2010-01-01'
stocks = ['2330.TW', '3443.TW', '2002.TW', '2317.TW', '2731.TW', '3687.TWO']

# Create an empty DataFrame to store stock data
all_stock_data = pd.DataFrame()

for stock_no in stocks:
    stock = yf.Ticker(stock_no)
    stock_data = stock.history(start=date)
    
    # Check if stock_data is empty or the stock data is missing
    if stock_data.empty or 'Close' not in stock_data.columns:
        print(f"Data for {stock_no} not found or possibly delisted.")
        stock_data = pd.DataFrame(index=pd.date_range(start=date, periods=1), columns=[stock_no])
    else:
        stock_data = stock_data[['Close']]  # Selecting only the 'Close' column
        stock_data.rename(columns={'Close': stock_no}, inplace=True)  # Renaming the column to the stock number
    
    # Remove timezone information from the datetime index
    stock_data.index = stock_data.index.tz_localize(None)
    
    # Combine the data
    if all_stock_data.empty:
        all_stock_data = stock_data
    else:
        all_stock_data = all_stock_data.join(stock_data, how='outer')

# Remove timezone information from the datetime index
all_stock_data.index = all_stock_data.index.tz_localize(None)

# Write to Excel file
output_path = './StockData/daily_price.xlsx'
all_stock_data.to_excel(output_path)
