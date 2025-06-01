# 漲Llama ! AI股市分析服務 • 金融科技實驗室

## 專案概述
本專案「漲Llama！」旨在透過結合 RAG 技術、Prompt Engineering 與資料壓縮處理，對股票基本面與新聞輿論進行深度分析，為使用者提供一個可解釋且穩健的投資建議分數。整體架構採用前後端分離設計，後端以 Flask 建構 RESTful API，AI 模型運行於 GCP 伺服器環境。最終成果透過隨機森林驗證回報率略高於大盤，且波動幅度較小，展現了模型的穩定性與有效性。

---

## 技術棧
- **前端（使用者介面）**  
  - HTML、JavaScript、Bootstrap  
  - 資料視覺化：Chart.js（或 D3.js）呈現情緒長條圖、股價走勢圖等

- **後端 API**  
  - Python 3.10+、Flask  
  - RESTful API 設計（前後端分離）  
  - 部署平台：Google Cloud Platform (GCE / GKE)

- **AI 模型分析**  
  - 文本情感分析：BERT（基於 Hugging Face Transformers）  
  - 規則邏輯與財務指標：自訂 Python 邏輯與 pandas、scikit-learn  
  - 向量檢索（RAG）：OpenAI Embedding API + 本地向量儲存（可擴展為 Faiss、Pinecone 等）  
  - 輔助驗證：隨機森林 (Random Forest) 回測模型表現

- **資料蒐集與資料庫**  
  - 網路爬蟲：Scrapy、requests、BeautifulSoup  
  - 資料庫：MySQL  
  - 資料來源：財經新聞網站、公開資訊觀測站 (公開資訊觀測站API)  
  - 資料清洗：pandas  

- **部署與環境管理**  
  - 本機測試環境、Docker Container（可擴展至 GCP 上的 Kubernetes 或 Compute Engine）  
  - 虛擬環境管理：venv + pip（`requirements.txt`）  
  - 版本控制：Git / GitHub

---

## 專案成果
- **回測結果**：  
  - 以隨機森林驗證投資策略，回報率略高於大盤基準，且波動幅度相對較小。  
  - 平均年化報酬率達 X%、最大回撤控制在 Y% 以內（示例數值，請依實際測試結果更新）。

- **關鍵特色**：  
  1. **結合新聞情緒與財報健康度**：  
     - 使用 BERT 模型進行新聞情感分類（正面 / 中立 / 負面），並根據財報指標計算企業健康度。  
     - 最終綜合生成 -10 到 +10 的投資建議分數，數值越高代表越強烈的買進建議。

  2. **RAG 技術加速資訊檢索**：  
     - 透過 OpenAI Embedding API 將新聞文本向量化，並在本地向量庫中進行最近鄰檢索，快速找出最相關的上下文，供 LLM 進行分析。  
     - 透過 Prompt Engineering 將檢索結果與財務數據整合，提供更具解釋性的回應。

  3. **前後端分離、可擴展架構**：  
     - 使用 Flask 提供 RESTful API，前端僅需撰寫 AJAX / Fetch 呼叫即可取得分析結果。  
     - 後端可快速擴充新的模型或資料來源；前端可自由更換技術（如 Vue、React）而不影響後端邏輯。

---

## 功能說明

### 1️⃣ 前端（使用者介面）
- **技術**：HTML + JavaScript + Bootstrap  
- **主要功能**：  
  1. **顯示個股情緒分析**  
     - 長條圖呈現過去一段期間內（如 30 天）新聞情感分布：正面 / 中立 / 負面。  
  2. **顯示個股財務資料**  
     - 抓取並顯示最新財報指標，如本益比 (P/E ratio)、毛利率、負債比率等。  
  3. **顯示新聞列表與快訊**  
     - 即時呈現最新相關新聞標題與摘要，點擊可查看完整內文。  
  4. **顯示股價走勢圖與投資建議分數**  
     - 折線圖顯示個股歷史收盤價走勢，並在圖上標示最近一次模型建議分數。  
  5. **互動性**  
     - 使用者可輸入股票代碼 → 前端發送 AJAX 請求至後端 → 更新頁面展示內容。

### 2️⃣ 後端 API
- **技術**：Flask（Python 框架）  
- **主要路由（示例）**：  
  1. **`GET /api/sentiment?symbol=<SYMBOL>&days=<N>`**  
     - 功能：取得輸入股票在過去 N 天內新聞情感分析結果（平均情感分數、各日分佈）。  
     - 回傳 JSON 範例：  
       ```json
       {
         "symbol": "2330.TW",
         "period_days": 30,
         "daily_sentiment": [
           { "date": "2025-05-30", "positive": 10, "neutral": 5, "negative": 3 },
           { "date": "2025-05-29", "positive": 8, "neutral": 7, "negative": 4 },
           …
         ],
         "average_score": 0.12
       }
       ```  

  2. **`GET /api/financials?symbol=<SYMBOL>`**  
     - 功能：取得該股票最新財報指標（由 MySQL 儲存並定期更新）。  
     - 回傳 JSON 範例：  
       ```json
       {
         "symbol": "2330.TW",
         "financials": {
           "PE_ratio": 25.3,
           "profit_margin": 0.38,
           "debt_ratio": 0.15,
           "ROE": 0.22
         }
       }
       ```

  3. **`GET /api/invest-score?symbol=<SYMBOL>`**  
     - 功能：綜合「新聞情感 + 財務健康度」生成投資建議分數 (-10 ~ +10)。  
     - 執行流程：  
       1. 從 `stock_news` 表取出最近 N 筆新聞 → 使用 BERT 得到情感分數。  
       2. 從 `stock_financials` 表取出最新財報指標 → 計算健康度分數。  
       3. 使用規則邏輯合併情感與財報，得到最終 -10 ~ +10 分數。  
       4. 可選：呼叫隨機森林模型驗證歷史表現，並將建議分數紀錄至 `investment_scores` 表。  
     - 回傳 JSON 範例：  
       ```json
       {
         "symbol": "2330.TW",
         "investment_score": 4,
         "explanation": "近期新聞情感偏正面 (平均情感 +0.15)，財報健康度 0.8，綜合後建議分數 +4。"
       }
       ```

  4. **`GET /api/related-news?symbol=<SYMBOL>&top_k=<K>`**  
     - 功能：使用 RAG 進行向量檢索，回傳最相關的 Top K 條新聞內容摘要。  
     - 執行流程：  
       1. 使用 OpenAI Embedding API 將使用者查詢（如「2330.TW 股票」）或關鍵詞向量化。  
       2. 在本地 MySQL 向量庫 (或 Faiss) 中檢索相似度最高的前 K 條新聞向量。  
       3. 回傳摘要與相似度分數。  
     - 回傳 JSON 範例：  
       ```json
       {
         "symbol": "2330.TW",
         "top_k": 3,
         "related_news": [
           {
             "news_id": 12345,
             "title": "台積電上季營收創新高，外資持續看好",
             "snippet": "…",
             "similarity_score": 0.87
           },
           {
             "news_id": 12346,
             "title": "半導體市場需求回溫，業界樂觀",
             "snippet": "…",
             "similarity_score": 0.84
           },
           …
         ]
       }
       ```

### 3️⃣ AI 模型分析
- **情感分析 (BERT)**  
  - 透過 Hugging Face Transformers 載入預訓練 BERT 模型，並微調於金融新聞語料庫上。  
  - 將新聞文本分類為正面 / 中立 / 負面，並回傳 Softmax 機率作為情感分數。

- **財務健康度計算**  
  - 根據最新財報指標 (P/E、毛利率、負債比、ROE 等)，設計一套「健康度」量化規則（例如：毛利率 > 30% → +2 分；負債比 < 20% → +1 分）。  
  - 最終將健康度標準化為 -5 ~ +5 範圍。

- **投資建議分數 (-10 ~ +10)**  
  - 將情感平均分數與財務健康度分數相加，若結果超過 ±10，則截取至 ±10。  
  - 例如：平均情感分數 3 (3/5scale) + 健康度 2 → 總分 5。若情感負面極度，則可能出現 -8、-9。

- **RAG 向量檢索**  
  - 利用 OpenAI Embedding API 將新聞或使用者查詢向量化 (Dimension=1536)。  
  - 在本地 MySQL 中儲存新聞向量欄位 (向量欄位可透過 JSON/Text 存放，或擴充為專用向量欄位)。  
  - 使用綜合距離計算 (如餘弦相似度) 找出最相關的上下文段落，並提供給前端或後續 LLM Prompt 參考。

- **回測驗證 (Random Forest)**  
  - 收集歷史資料 (新聞情感+財務指標+股價走勢)，建立特徵集 → `RandomForestClassifier` 或 `RandomForestRegressor` 回測策略  
  - 評估指標：年化報酬率、Sharpe ratio、最大回撤等。  
  - 結果呈現在 `/backtest` 內部腳本，並將回測結果匯出為可視化圖表 (Matplotlib)。

### 4️⃣ 資料收集與資料庫
- **Python 爬蟲 (Scrapy)**  
  1. `news_spider.py`：定期爬取財經新聞網站（如 Yahoo Finance、MoneyDJ、經濟日報等）  
     - 擷取新聞標題、發佈日期、新聞內文、連結等  
     - 依據股票代碼標記新聞屬性  
  2. `financial_spider.py`：爬取公開資訊觀測站 (公開資訊觀測站 API) 中公開公司財報資料  
     - 擷取季度報表、營收、淨利、EPS 等財務指標  
  3. 爬蟲執行後自動進行資料清洗 (清除 HTML 標籤、補齊缺失值)，使用 pandas 轉換為 DataFrame → 匯入 MySQL。

- **MySQL 資料庫設計**  
  - `stock_news` table：儲存原始新聞 (news_id, symbol, title, content, published_date)  
  - `stock_news_sentiment` table：儲存情感分析結果 (news_id, positive_prob, neutral_prob, negative_prob, sentiment_label)  
  - `stock_financials` table：儲存公司最新財報指標 (symbol, report_date, PE_ratio, gross_margin, debt_ratio, ROE, …)  
  - `news_vectors` table：儲存新聞向量化結果 (news_id, vector)`  
  - `investment_scores` table：儲存產生的投資分數歷史紀錄 (symbol, calculated_date, score, explanation)  

---

## 專案結構
