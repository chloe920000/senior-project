# prompt_generator.py 用來把股票資料塞進prompt裡面

def generate_message_content(stock_id, bps_str, capital_str, roe_str, eps_str, GM_str, OPM_str, DBR_str, summary_str, stock_price, company_background):
    return f'''Evaluate the stock price of TWSE{stock_id} based on the following data:
* The following data is from left to right, with the years from farthest to most recent.
* BPS (book value per share) over last 5 years: {bps_str}
* Capital over last 5 years: {capital_str} * 100 million
* ROE (return on equity) over last 5 years: {roe_str}%

* EPS (earnings per share) over last 5 years: {eps_str}

* GM (gross margin) over last 5 years: {GM_str}%
* OPM (operating profit margin) over last 5 years: {OPM_str}%
* DBR (debt-to-assets ratio) over last 5 years: {DBR_str}%
* Reference historical prices:
{summary_str}
* Current price: {stock_price}

Provide additional context about the company, industry, and market trends.

* Company Background:
{company_background}

Assume you are a stock analyst, provide answers to the following questions (Only answer the following questions, do not give suggestions or analysis):

1. Will it be bullish or bearish in the next six months?
2. Recommended buying price, considering a margin of error of +/- 5%?
3. Recommended selling price, assuming a stop-loss strategy with a maximum loss of 10%?
4. Recommended holding period for this investment?(months)
5. Suggested stop-loss strategy? What would be your criteria for triggering a sell order?

Criteria for evaluation:

* A "bullish" market is defined as an increase of at least 10% in the stock's price over the next six months.
* A "bearish" market is defined as a decrease of at least 15% in the stock's price over the next six months.
* If it is bullish, usually the selling price will be higher than the buying price. 
* If it is bearish, you do not need to answer question 2.3.4.5
* The Recommended selling price should be the take-profit price when bullish. If the former is bearish, it can be skipped directly.

Answer according to the example format, do not explain
answer example format:
1. Will it be bullish or bearish in the next six months?: Bullish/Bearish
2. Recommended buying price, considering a margin of error of +/- 5%?: [a integer] NTD
3. Recommended selling price, assuming a stop-loss strategy with a maximum loss of 10%?: [a integer] NTD
4. Recommended holding period for this investment? (months): [a integer] months
5. Suggested stop-loss strategy? What would be your criteria for triggering a sell order?: [strategy]
'''
