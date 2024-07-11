# 營業利益 (年度)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import pandas as pd
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import time
from stock import values

options = Options()
options.add_argument("--disable-notifications")

driver = webdriver.Chrome(options=options)
driver.implicitly_wait(15)

df = pd.DataFrame()
stock3 = ["2002", "2330", "2317", "2731", "3443", "3687"]
# , "3443", "2317", , "3687"
for stock_id in stock3[0:6]:
    # for stock_id in values[0:1]:

    print("Processing stock ID:", stock_id)
    url = f"https://goodinfo.tw/tw/StockBzPerformance.asp?STOCK_ID={stock_id}"

    driver.get(url)

    # Assuming 'driver' is your Selenium WebDriver instance
    wait = WebDriverWait(driver, 10)
    # Wait for either the element with ID "tblDetail" to be present or find the div with ID "txtFinDetailData" using Beautiful Soup
    element_present = wait.until(
        EC.presence_of_element_located((By.ID, "tblDetail"))
        or soup.find("div", {"id": "txtFinDetailData"})
    )

    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")

    ############# Find the main table #############
    table = soup.find("table", {"id": "tblDetail"})
    div_txtFinDetailData = soup.find("div", {"id": "txtFinDetailData"})

    if table:  # and div_txtFinDetailData.text.strip() != "查無資料":

        print("# " + str(stock_id))

        # Find the first th element with rowspan="2"
        first_row_th = (
            table.find("tr", {"class": "bg_h2"})
            .find("th", {"rowspan": "2"})
            .text.strip()
        )

        second_row_th = table.find_all("tr", {"class": "bg_h2"})[1].find_all("th")[9]
        second_row_th_texts = [th.text.strip() for th in second_row_th]

        # Output the result
        title = f"{first_row_th} {' '.join(second_row_th_texts)}"
        # print(title)

        time.sleep(1)

        # Find all tr elements with align="center"
        trs = table.find_all("tr", {"align": "center"})

        # Extract the text content of the first, ninth, and tenth td elements
        result = []
        year = []
        for tr in trs:
            tds = tr.find_all("td")
            if len(tds) >= 12:
                year.append(f"{tds[0].text.strip()}")
                result.append(f" {tds[13].text.strip()}")

        # Convert the result to a string
        year_str = "\n".join(year)
        result_str = "\n".join(result)

        # Output the result
        # for item in result:
        # print(item)
        # print("\n")

        new_data = {
            "Year": year_str.split("\n"),
            f"{stock_id}": result_str.split("\n"),
        }
        df_temp = pd.DataFrame(new_data)
        df = pd.concat([df, df_temp], axis=1)  # Concatenate the new data as new columns

        print(df)  # Print the DataFrame after each concatenation

        time.sleep(5)  # Add a delay between requests to avoid being blocked


# Save the DataFrame to a CSV file
df.to_csv(
    r"C:\Users\ziwei\source\GraduateProject\senior-project-main\stock_crawling_li\stocks_info\yOPM.csv",
    index=False,
)
print("success to save yOPM.csv")
driver.quit()
