# 營業利益率 (季度)
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
import pandas as pd
from selenium.webdriver.support.ui import Select
import re
from stock import values

options = Options()
options.add_argument("--disable-notifications")

driver = webdriver.Chrome()
driver.implicitly_wait(10)


df = pd.DataFrame()
stock3 = ["2002", "2330", "3443"]

for stock_id in stock3[0:3]:
    # for stock_id in values[0:1]:
    print("Processing stock ID:", stock_id)
    url = f"https://goodinfo.tw/tw/StockFinDetail.asp?RPT_CAT=XX_M_QUAR_ACC&STOCK_ID={stock_id}"
    driver.get(url)

    html = driver.page_source
    soup = BeautifulSoup(html, "lxml")

    #############下拉式選單#############
    select = soup.find_all("select", {"id": "QRY_TIME"})
    # print(select)
    z = []
    # 遍歷所有找到的下拉式選單
    for k in select:
        # 找到該選單中的所有option標籤
        op = k.find_all("option")
        # 遍歷所有option標籤
        for i in range(len(op)):
            # 將每個option標籤的文字內容添加到列表z中
            z.append(op[i].text)  # 所有選單選項
    # print(z)

    # 要click的選項
    click = []
    # 從索引0開始，每10個選項取一次
    for i in range(0, len(z), 10):
        # print(z[i])
        # 將取得的選項添加到click列表中
        click.append(z[i])

    # 不保留Q(因為他的value沒有Q)
    # 使用正則表達式將每個選項中的非數字字符替換為空白，並加入到result列表中
    result = [re.sub(r"\D", "", item) for item in click]
    print(result)

    # 選擇下拉式選單
    for value in result:
        ele = driver.find_element("id", "QRY_TIME")
        select = Select(ele)

        for option in select.options:
            if option.get_attribute("value") == value:
                option.click()
                time.sleep(6)
                break

        html = driver.page_source
        soup = BeautifulSoup(html, "lxml")

        # 初始化
        x = []
        y = []

        # 季度(當index)
        year = soup.find_all("tr", {"class": "bg_h1 fw_normal"})
        # 找到"獲利能力"該行
        for i in year[3]:
            f_nobr = i.find_all("nobr")
            for nobr in f_nobr:
                # print(nobr.text)
                x.append(nobr.text)
        # print(x)
        time.sleep(5)

        # TABLE(營業利益率)
        table = soup.find_all(
            "tr", {"bgcolor": "white", "align": "right", "valign": "middle"}
        )
        for j in table[1]:
            f_nobr = j.find_all("nobr")
            for nobr in f_nobr:
                y.append(nobr.text)

        print(pd.Series(y[1:], index=x[1:]))
        data = pd.Series(y[1:], index=x[1:])
        df[f"Stock {stock_id}"] = data
        # x = []
        # y = []
        time.sleep(5)


time.sleep(3)
# Save the DataFrame to a CSV file
df.to_csv(
    r"C:\Users\ziwei\source\GraduateProject\crawler\stocks_info\sOPM.csv", index=False
)
print("success to save sOPM.csv")
driver.quit()
