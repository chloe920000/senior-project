import asyncio
import pandas as pd
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import os
import csv
from dotenv import load_dotenv
from supabase import create_client, Client
from ollama import AsyncClient

from get_prompt_data import *
from prompt_generater import *

# Define the four specific dates
dates = ["2022-09-07", "2022-04-19", "2020-11-13", "2023-06-07"]

# Get the directory of the script
script_dir = os.path.dirname(os.path.abspath(__file__))

# Set the relative path for the result data
result_data_dir = os.path.join(script_dir, "..", "analyze result")
if not os.path.exists(result_data_dir):
    os.makedirs(result_data_dir)

# Load environment variables
load_dotenv()
# Initialize Supabase client
url: str = os.environ.get("SUPABASE_URL")
key: str = os.environ.get("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Function to parse model output
import re


def parse_output(output):
    result = {}
    # Regular expressions to match each question's answer
    bullish_match = re.search(
        r"1\. Is the next six months bullish or bearish\?:(.*)", output
    )
    buy_recommendation_match = re.search(
        r"2\. Based on the current price, is it recommended to buy\?\s*:(.*)", output
    )
    sell_price_match = re.search(
        r"3\. Based on the current price, assuming the maximum loss of the stop loss strategy is 10%, what is the recommended selling price\?\s*:(.*)",
        output,
    )
    holding_period_match = re.search(
        r"4\. What is the recommended holding period for this investment\?\s*\(month\):\s*(.*)",
        output,
    )
    stop_loss_strategy_match = re.search(
        r"5\. Suggested stop loss strategy\? What are your criteria for triggering a sell order\?\s*:(.*)",
        output,
    )

    if bullish_match:
        result["Bullish/Bearish"] = bullish_match.group(1).strip()
    if buy_recommendation_match:
        result["Recommend buy or not"] = buy_recommendation_match.group(1).strip()
    if sell_price_match:
        result["Recommended selling price"] = sell_price_match.group(1).strip()
    if holding_period_match:
        result["Recommended holding period"] = holding_period_match.group(1).strip()
    if stop_loss_strategy_match:
        result["Stop-loss strategy"] = stop_loss_strategy_match.group(1).strip()

    return result


async def chat():
    # Get all stockIDs
    stock_ids = supabase.table("stock").select("stockID").execute()
    stock_ids = [record["stockID"] for record in stock_ids.data]

    # Iterate over each stockID
    for stock_id in stock_ids:
        for date in dates:
            end_year = int(date[:4])
            start_year = end_year - 4

            # Get data needed for prompt
            result = select_supabase_data(stock_id, date)
            data_bps = result["data_bps"]
            data_roe = result["data_roe"]
            data_Share_capital = result["data_Share_capital"]
            data_eps = result["data_eps"]
            data_GM = result["data_GM"]
            data_OPM = result["data_OPM"]
            data_DBR = result["data_DBR"]
            data_roa = result["data_roa"]
            data_per = result["data_per"]
            stock_price = result["stock_price"]

            # Summarize historical stock data
            yearly_summary = summarize_stock_data(stock_id, end_year)
            summary_str = get_stock_summary_string(yearly_summary)

            # Get company background data
            company_background = get_company_background(stock_id)

            # Process data
            bps_values = [
                safe_get_value(data_bps, year, "BPS")
                for year in range(start_year, end_year + 1)
            ]
            roe_values = [
                safe_get_value(data_roe, year, "ROE")
                for year in range(start_year, end_year + 1)
            ]
            capital_values = [
                safe_get_value(data_Share_capital, year, "Share_Capital")
                for year in range(start_year, end_year + 1)
            ]
            roa_values = [
                safe_get_value(data_roa, year, "roa")
                for year in range(start_year, end_year + 1)
            ]
            eps_values = [
                safe_get_value(data_eps, year, "EPS")
                for year in range(start_year, end_year + 1)
            ]
            per_values = [
                safe_get_value(data_per, year, "per")
                for year in range(start_year, end_year + 1)
            ]
            GM_values = [
                safe_get_value(data_GM, year, "GM")
                for year in range(start_year, end_year + 1)
            ]
            OPM_values = [
                safe_get_value(data_OPM, year, "OPM")
                for year in range(start_year, end_year + 1)
            ]
            DBR_values = [
                safe_get_value(data_DBR, year, "DBR")
                for year in range(start_year, end_year + 1)
            ]

            # Convert data to string format
            bps_str = ", ".join(map(str, bps_values))
            roe_str = ", ".join(map(str, roe_values))
            capital_str = ", ".join(map(str, capital_values))
            roa_str = ", ".join(map(str, roa_values))
            eps_str = ", ".join(map(str, eps_values))
            per_str = ", ".join(map(str, per_values))
            GM_str = ", ".join(map(str, GM_values))
            OPM_str = ", ".join(map(str, OPM_values))
            DBR_str = ", ".join(map(str, DBR_values))

            print("bps_str:", bps_str)
            print("roe_str:", roe_str)
            print("capital_str:", capital_str)
            print("roa_str:", roa_str)
            print("eps_str:", eps_str)
            print("per_str:", per_str)
            print("GM_str:", GM_str)
            print("OPM_str:", OPM_str)
            print("DBR_str:", DBR_str)
            print("summary_str:", summary_str)
            print("current price:", stock_price)
            print("company background:", company_background)

            # --------------------------------循環次數------------------------------------ #
            for _ in range(1):
                stock_price = get_stock_price(stock_id, date)

                # Generate message content using the function
                message_content = generate_message_content(
                    stock_id,
                    bps_str,
                    capital_str,
                    roe_str,
                    eps_str,
                    GM_str,
                    OPM_str,
                    DBR_str,
                    summary_str,
                    stock_price,
                    company_background,
                )

                # Save input message to log file
                input_log_path = os.path.join(
                    result_data_dir, stock_id, f"input_log_{stock_id}.txt"
                )

                # Ensure the directory exists
                os.makedirs(os.path.dirname(input_log_path), exist_ok=True)

                with open(input_log_path, "a", encoding="utf-8") as input_log_f:
                    input_log_f.write(f"no.{_} === {datetime.now()} ===\n")
                    input_log_f.write(f"Date: {date}\n")
                    input_log_f.write(message_content)
                    input_log_f.write("\n\n")

                message = {"role": "user", "content": message_content}

                # Modify paths
                result_path = os.path.join(
                    result_data_dir, stock_id, f"output_{stock_id}.txt"
                )
                log_path = os.path.join(
                    result_data_dir, stock_id, f"output_log_{stock_id}.txt"
                )
                csv_path = os.path.join(
                    result_data_dir, stock_id, f"output_{stock_id}.csv"
                )

                # Ensure the directory exists
                os.makedirs(os.path.dirname(result_path), exist_ok=True)

                fieldnames = [
                    "Date",
                    "Bullish/Bearish",
                    "Recommend buy or not",
                    "Recommended selling price",
                    "Recommended holding period",
                    "Stop-loss strategy",
                ]

                # Save output as a txt file
                with open(result_path, "w", encoding="utf-8") as f:
                    async for part in await AsyncClient().chat(
                        model="llama3.1:8B",
                        messages=[message],
                        stream=True,
                        options={"temperature": 0.3},
                    ):
                        f.write(part["message"]["content"])

                # Parse the output
                with open(result_path, "r", encoding="utf-8") as f:
                    output = f.read()
                    parsed_result = parse_output(output)
                    parsed_result["Date"] = date  # Add the date to the parsed result

                # Write results to CSV
                # Check if CSV file exists
                try:
                    with open(csv_path, "x", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                except FileExistsError:
                    pass

                # Append the parsed result to the CSV file
                with open(csv_path, "a", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writerow(parsed_result)

                # Save historical record to log file
                with open(log_path, "a", encoding="utf-8") as log_f:
                    log_f.write(f"no.{_} === {datetime.now()} ===\n")
                    log_f.write(output)
                    log_f.write("\n\n")

                # Output results to terminal
                print(_)
                print(parsed_result)


asyncio.run(chat())
