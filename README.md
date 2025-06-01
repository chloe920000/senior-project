# Stock Market Analysis Project

## Project Overview
This project is designed to analyze stock market data and provide insights using advanced natural language processing techniques. It leverages Supabase for structured financial data storage and retrieval, and integrates with language models to generate predictions and sentiment analysis based on financial data and news articles.

## Key Features
- **Supabase Integration**: Access structured financial data directly from Supabase.
- **Sentiment Analysis**: Analyze stock-related news articles to determine market sentiment.
- **Language Model Predictions**: Generate predictions and insights using OpenAI's language models.
- **Modular Design**: Well-structured codebase for easy extension and maintenance.

## Setup Instructions
1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/senior-project.git
   ```
2. Navigate to the project directory:
   ```bash
   cd senior-project
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up Supabase credentials:
   - Create a `.env` file in the root directory.
   - Add your Supabase URL and API key:
     ```env
     SUPABASE_URL=<your-supabase-url>
     SUPABASE_KEY=<your-supabase-key>
     ```
5. Run the application:
   ```bash
   python llama_flask/llama_main_TogetherFlask.py
   ```

## Usage Instructions
- Access the application via the provided Flask endpoint.
- Use the interface to query stock data and generate predictions.
- Analyze sentiment scores for stock-related news articles.

## Architecture and Workflow
1. **Data Retrieval**:
   - Financial data is fetched from Supabase using functions like `select_supabase_data()`.
   - News articles are crawled and processed for sentiment analysis.
2. **Data Processing**:
   - Sentiment analysis is performed using `sentiment_analysis.py`.
   - Prompts are generated for the language model using `get_prompt_data.py`.
3. **Prediction Generation**:
   - The language model generates predictions based on the processed data.

## Future Enhancements
- **RAG Integration**:
  - Use OpenAI's embedding API to vectorize financial reports and news articles.
  - Store vectorized data in a vector database for semantic search.
  - Enhance prediction accuracy by retrieving relevant context during prompt generation.
- **Improved Sentiment Analysis**:
  - Incorporate more advanced sentiment analysis techniques.
- **User Interface**:
  - Develop a user-friendly web interface for better accessibility.



---
Feel free to contribute to the project by submitting issues or pull requests!
