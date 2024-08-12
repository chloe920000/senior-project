函數詳細說明
1. get_stock_price(stock_id)
功能：

獲取指定股票代碼的即時價格資訊，包括股票名稱、當前價格及價格變化狀態（上漲、下跌或持平）。
參數：

stock_id：股票代碼（例如 '8305'）。
操作：

使用 requests 獲取 Yahoo Finance 上該股票的網頁內容。
使用 BeautifulSoup 解析 HTML。
從 HTML 中提取股票名稱和當前價格。
根據價格變化類型（上漲、下跌、持平）設置狀態。
返回格式化的股票資訊字串。

2. get_company_background(stock_id)
功能：

獲取指定股票代碼的公司背景資料。
參數：

stock_id：股票代碼（例如 '8305'）。
操作：

使用 requests 獲取 Yahoo Finance 上該股票的公司資料頁面。
使用 BeautifulSoup 解析 HTML。
查找並提取公司背景資料部分。
返回公司背景資料字串，如果無法取得則返回預設文字「無法取得公司背景資料」。

3. parse_output(output)
功能：

解析模型生成的預測結果，提取關鍵資訊。
參數：

output：模型生成的文本輸出字串。
操作：

將輸出文本按行分割。
根據文本內容提取並分類預測結果，包括股票市場趨勢、推薦買入和賣出價格、建議持有期限及止損策略。
返回提取的結果字典。

4. summarize_stock_data(file_path, stock_id, end_year)
功能：

彙總指定股票在 CSV 文件中的歷史價格數據，按年度計算開盤價、收盤價、最高價和最低價。
參數：

file_path：包含歷史價格數據的 CSV 文件路徑。
stock_id：股票代碼。
end_year：要計算的最後年份。
操作：

使用 pandas 讀取 CSV 文件，並將日期列設置為索引。
過濾出指定年份及之前的數據。
按年度對數據進行匯總，計算開盤價、收盤價、最高價和最低價。
返回彙總的數據框。

5. get_stock_summary_string(summary)
功能：

將股票數據彙總轉換為易於閱讀的字串格式。
參數：

summary：由 summarize_stock_data 函數返回的數據框。
操作：

將每年的價格數據格式化為字串。
將所有年度數據合併為一個字串，並返回。

6. get_data_from_supabase(table_name, stock_id, start_year, end_year)
功能：

從 Supabase 獲取指定股票的歷史財務數據。
參數：

table_name：數據表名稱（例如 'year_bps'）。
stock_id：股票代碼。
start_year：起始年份。
end_year：結束年份。
操作：

使用 Supabase 客戶端發送請求以獲取指定股票在指定年份範圍內的數據。
將獲取到的數據轉換為 pandas 數據框。
返回數據框。

7. chat()
功能：

執行整個股票分析流程，包括數據提取、處理、預測報告生成和結果儲存。
操作：

設置股票代碼和年份範圍。
從 Supabase 獲取各類財務數據。
彙總股票歷史數據並獲取公司背景資料。
構建並發送包含所有數據的預測請求給 Ollama。
將 Ollama 的回應寫入 TXT 和 CSV 文件中。
輸出結果到終端。
