StockNewsCrawling
此資料夾包含用於股票新聞爬蟲與情緒分析的 Python 程式碼，以下是各個檔案的說明：

爬蟲程式碼
這些程式碼負責從不同新聞網站抓取與股票相關的新聞資料，並將資料整理後儲存於指定的資料庫中：

1.crawler_chinatime_to_supa.py
從《中國時報》網站抓取新聞資料，並將資料儲存到 SUPA 平台。

2.crawler_cnye_to_supa.py
從《中時電子報》網站抓取新聞資料，並將資料儲存到 SUPA 平台。

3.crawler_Itn_to_supa.py
從《經濟日報》網站抓取新聞資料，並將資料儲存到 SUPA 平台。

3.crawler_tvbs_to_supa.py
從《TVBS》網站抓取新聞資料，並將資料儲存到 SUPA 平台。

情緒分析程式碼
這些程式碼負責分析抓取到的新聞資料中的情緒，並將分析結果與股市訊號結合：

sentiment_analysis_to_supa.py
使用 cvaw3 和 NTUD 情緒分析字典來分析新聞文本的情緒，並將結果儲存到 SUPA 平台。

gemini_signal_to_supa.py
負責處理 Gemini 模型的股市訊號，並將訊號結果儲存到 SUPA 平台。

設定檔
settings.py
包含 Gemini 模型的相關設定，如 API 金鑰、資料庫連接資訊等。