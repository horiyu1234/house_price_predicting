import time
import os
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup

def extract_property_info(property_soup):
    property_info_list = []

    try:
        property_name = property_soup.select_one('.property-detail-content__head-title a')
        property_name = property_name.get_text(strip=True) if property_name else ''

        address = access = age = ''
        info_table = property_soup.find('table', class_='property-detail-content_main')
        if info_table:
            for row in info_table.find_all('tr'):
                th = row.find('th')
                td = row.find('td')
                if not th or not td:
                    continue
                key = th.get_text(strip=True)
                val = td.get_text(separator=' ', strip=True)
                if key == '住所':
                    address = val
                elif key == '交通':
                    access = val
                elif key == '築年数':
                    age = val

        recommend_tables = property_soup.find_all('table', class_='recommendTable')
        for table in recommend_tables:
            for tbody in table.find_all('tbody', class_='recommend_row'):
                tr = tbody.find('tr')
                if not tr:
                    continue
                tds = tr.find_all('td')
                if len(tds) < 9:
                    continue

                image_tag = tds[0].find('img')
                image_url = image_tag.get('data-original') if image_tag else ''

                room_name = tds[1].get_text(strip=True)
                rent = tds[2].get_text(strip=True)
                deposit = tds[3].get_text(strip=True)
                key_money = tds[4].get_text(strip=True)
                area = tds[5].get_text(strip=True)
                floor_plan = tds[6].get_text(strip=True)
                floor = tds[7].get_text(strip=True)
                facing = tds[8].get_text(strip=True)

                property_info_list.append({
                    '物件名': property_name,
                    '住所': address,
                    '交通': access,
                    '築年数': age,
                    '部屋名': room_name,
                    '賃料': rent,
                    '敷金': deposit,
                    '礼金': key_money,
                    '占有面積': area,
                    '間取り': floor_plan,
                    '所在階': floor,
                    '向き': facing,
                    '画像': image_url
                })
    except Exception as e:
        print(f"Error extracting property info: {e}")

    return property_info_list

def scrape_paginated_properties(base_url, max_pages=10, wait_sec=60):
    all_properties = []

    # ChromeDriverのパス
    driver_path = '/Users/yhorii/Documents/Pythoncode/chromedriver-mac-arm64/chromedriver'

    chrome_options = Options()
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36")

    service = Service(executable_path=driver_path)
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        for page_num in range(1, max_pages + 1):
            url = base_url if page_num == 1 else f"{base_url.rstrip('.html')}_{page_num}.html"
            print(f"Fetching: {url}")

            driver.get(url)
            time.sleep(wait_sec)

            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')

            result_block = soup.find("div", id="resultBlock")
            if not result_block:
                print(f"Skipped: page {page_num} has no resultBlock")
                continue

            properties = result_block.select('section.chart_list_layout')
            for prop in properties:
                all_properties.extend(extract_property_info(prop))
    finally:
        driver.quit()

    return pd.DataFrame(all_properties)

if __name__ == "__main__":
    BASE_URL = "https://www.mansion-review.jp/chintai/city/678.html"
    df = scrape_paginated_properties(BASE_URL, max_pages=1000, wait_sec=60)

    output_path = "nerima_scraped_mansion_data.csv"
    df.to_csv(output_path, index=False)
    print(f"Saved to {output_path} ({len(df)} rows)")
