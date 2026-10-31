import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime

url = "https://www.jalan.net/uw/uwp3200/uww3201init.do?vos=hajlnxggfrzzx00000002&yadNo=321582&roomCount=1&roomCrack=100000&stayCount=1&stayYear=2026&stayMonth=05&stayDay=30&planCd=04309756&roomTypeCd=0241483&adultNum=2&isDeepLink=1"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

price_element = soup.select_one(".p-planOverview__charge em")

# 今日の日付取得
today = datetime.now().strftime("%Y/%m/%d")

if price_element:
    price_text = price_element.get_text(strip=True)
    price = int(re.sub(r"\D", "", price_text))

    print(f"{today} の東京ビジネスホテルのじゃらん価格: {price}円")

else:
    print("価格が見つかりませんでした")