import datetime
import math
import random
from decimal import Decimal
from typing import List

import scrapy
from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException, NoSuchElementException
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from real_estate_trade_price.items import RealEstateTradePriceItem

text_search_css = '#BodyLeft > ul > li:nth-child(2)'  # css selector of 純文查詢
choose_district_id = 'ContentPlaceHolder1_ContentPlaceHolder1_TruePriceSearch1_cblArea_'  # part id of 行政區 checkbox
trade_start_year_id = 'ContentPlaceHolder1_ContentPlaceHolder1_TruePriceSearch1_ddl_TransactionStartYear'  # id of 交易年月 start year
trade_start_month_id = 'ContentPlaceHolder1_ContentPlaceHolder1_TruePriceSearch1_ddl_TransactionStartMonth'  # id of 交易年月 start month
trade_end_year_id = 'ContentPlaceHolder1_ContentPlaceHolder1_TruePriceSearch1_ddl_TransactionEndYear'  # id of 交易年月 end year
trade_end_month_id = 'ContentPlaceHolder1_ContentPlaceHolder1_TruePriceSearch1_ddl_TransactionEndMonth'  # id of 交易年月 end month

end_year_default = datetime.datetime.now().year - 1911
end_month_default = datetime.datetime.now().month
if end_month_default < 3:
    start_year_default = end_year_default - 1
    start_month_default = end_month_default + 10
else:
    start_year_default = end_year_default
    start_month_default = end_month_default - 2
start_district_no_default = 0
end_district_no_default = 11

search_btn_id = 'ContentPlaceHolder1_ContentPlaceHolder1_TruePriceSearch1_btn_Search'  # id of 查詢 button
table_id = 'ContentPlaceHolder1_ContentPlaceHolder1_gvTruePrice_A_gv_TruePrice'  # id of table
total_rows_id = 'ContentPlaceHolder1_ContentPlaceHolder1_gvTruePrice_A_lbl_totalCount'  # id of total count of rows
more_info_css_list = ['#lbl_buildA', '#lbl_ManagerA', '#div_A_Land tr:nth-child(2) > td:nth-child(4)',  # list of elements in more information want to get
                      '#div_A_Build tr:nth-child(2) > td:nth-child(5)', '#div_A_Note td']


class GetTpBuildingsAndLandSpider(scrapy.Spider):
    name = 'get_tp_buildings_and_land'
    allowed_domains = ['cloud.land.gov.taipei/ImmPrice']
    start_urls = ['https://cloud.land.gov.taipei/ImmPrice/TruePriceA.aspx']

    def __init__(self, start_year=start_year_default, start_month=start_month_default,
                 end_year=end_year_default, end_month=end_month_default,
                 start_district_no=start_district_no_default, end_district_no=end_district_no_default, *args, **kwargs):
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')

        super().__init__(*args, **kwargs)
        self.start_year = int(start_year)
        self.start_month = int(start_month)
        self.end_year = int(end_year)
        self.end_month = int(end_month)
        self.start_district_no = int(start_district_no)
        self.end_district_no = int(end_district_no)
        self.driver = webdriver.Chrome(chrome_options=chrome_options)
        self.wait = WebDriverWait(self.driver, 600, 0.01)
        self.default_window = self.driver.current_window_handle

    def parse(self, response, **kwargs):
        driver = self.driver
        driver.get(response.url)

        driver.execute_script("document.getElementById('tab1').style.display = 'none';")
        driver.execute_script("document.getElementById('tab2').style.display = 'block';")

        for year in range(self.start_year, self.end_year + 1):  # every year
            fr = self.start_month if year == self.start_year else 1
            to = self.end_month if year == self.end_year else 12
            for month in range(fr, to + 1):  # every month
                for district_no in range(self.start_district_no, self.end_district_no + 1):  # every district
                    driver.execute_script(f"document.getElementById('{choose_district_id}{district_no}').checked = true;")
                    self._select_time_range(year, month)
                    self.driver.execute_script('arguments[0].click();', self.wait.until(EC.element_to_be_clickable((By.ID, search_btn_id))))

                    self.wait.until(EC.visibility_of_element_located((By.ID, table_id)))
                    district_name = self.driver.find_element(By.CSS_SELECTOR, f"#{choose_district_id}{district_no} ~ label").text + '區'
                    self.wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, f"#{table_id} > tbody > tr:nth-child(3) > td:nth-child(2)"), district_name))

                    total_rows = int(driver.find_element(By.ID, total_rows_id).text)
                    for page in range(1, math.ceil(total_rows / 10) + 1):  # every page
                        row_count = len(driver.find_elements(By.CSS_SELECTOR, f"#{table_id} > tbody > tr"))

                        for row_no in range(3, row_count + 1):  # every row in the table
                            table_td_list = driver.find_elements(By.CSS_SELECTOR, f"#{table_id} > tbody > tr:nth-child({row_no}) td")
                            yield self._list_to_item(table_td_list, district_name)

                        if page != math.ceil(total_rows / 10):
                            self._swap_table_page('...' if page % 10 == 0 else page + 1)

                    if total_rows > 10:    # swap to first page before starting new district
                        self._swap_table_page('第一頁' if total_rows > 100 else 1)
                    driver.execute_script(f"document.getElementById('{choose_district_id}{district_no}').checked = false;")

        driver.quit()

    def _select_time_range(self, year: int, month: int):
        self.driver.execute_script(f"document.getElementById('{trade_start_year_id}').value='{year}';")
        self.driver.execute_script(f"document.getElementById('{trade_start_month_id}').value='{str(month).zfill(2)}';")
        self.driver.execute_script(f"document.getElementById('{trade_end_year_id}').value='{year}';")
        self.driver.execute_script(f"document.getElementById('{trade_end_month_id}').value='{str(month).zfill(2)}';")

    def _list_to_item(self, table_td_list: List[WebElement], district_name: str) -> RealEstateTradePriceItem:
        item = RealEstateTradePriceItem()
        item['district'] = district_name
        addr = self._to_exact_addr(table_td_list[2].text)
        item['address'] = addr
        item['trade_date'] = self._roc_to_date(table_td_list[3].text)
        item['total_price'] = self._check_and_to_int(table_td_list[4].text, 10000)
        item['unit_price'] = self._check_and_to_float(table_td_list[5].text, 10000)
        item['unit_price_include_park'] = True if table_td_list[6].text == '是' else False
        item['building_area'] = self._check_and_to_float(table_td_list[7].text)
        item['land_area'] = self._check_and_to_float(table_td_list[8].text)
        item['building_type'] = table_td_list[9].text
        item['building_age'] = self._check_and_to_float(table_td_list[10].text)
        item['floor'] = self._check_and_to_int(table_td_list[11].text.split('/')[0].replace('全', '').replace('B', '-'))
        item['total_floor'] = self._check_and_to_int(table_td_list[11].text.split('/')[1].replace('全', ''))
        item['trade_include_park'] = True if table_td_list[11].text == '房地車' else False
        item['first_trade'] = 1 if table_td_list[14].text == '有' else 0

        self.driver.execute_script('arguments[0].click();', table_td_list[15].find_element(By.TAG_NAME, 'a'))
        more_info = self._get_more_info()
        item['building_layout'] = more_info[0]
        item['have_guard'] = True if more_info[1] == '有' else False
        item['land_type'] = more_info[2]
        item['building_material'] = more_info[3]
        item['remark'] = None if more_info[4] == '無' else more_info[4]

        return item

    def _swap_table_page(self, button_text: str):
        try:
            button = self.driver.find_element(By.XPATH, f"(//table[@id='{table_id}']//a[contains(text(), '{button_text}')])[last()]")
        except NoSuchElementException:
            button = self.driver.find_element(By.XPATH, f"(//table[@id='{table_id}']//a[contains(text(), '...')])[last()]")
        button.click()
        self.wait.until(EC.staleness_of(button))

    @staticmethod
    def _roc_to_date(date: str) -> datetime.date:
        year, month, day = date.split('/')
        return datetime.date(int(year) + 1911, int(month), int(day))

    @staticmethod
    def _check_and_to_int(text: str, multiple: int = 1):
        if text == '':
            return None
        else:
            return int(Decimal(text.replace(',', '')) * Decimal(str(multiple)))

    @staticmethod
    def _check_and_to_float(text: str, multiple: int = 1):
        if text == '':
            return None
        else:
            return float(Decimal(text.replace(',', '')) * Decimal(str(multiple)))

    @staticmethod
    def _to_exact_addr(text: str) -> str:
        end = text.find('號')
        if len(text) < end + 3 or (text[end + 2] != '單' and text[end + 2] != '雙'):
            odd_even = random.choice(['單', '雙'])
        else:
            odd_even = text[end + 2]
        no_brackets_text = text[end - 1::-1]
        for idx, char in enumerate(no_brackets_text):
            if char == '-':
                dash_idx = idx
                to = int(no_brackets_text[dash_idx - 1::-1])
            elif not char.isdigit():
                try:
                    fr = int(no_brackets_text[idx - 1:dash_idx:-1])
                    if (odd_even == '單' and fr % 2 == 1) or (odd_even == '雙' and fr % 2 == 0):
                        return no_brackets_text[:idx - 1:-1] + str(random.randrange(fr, to + 1, 2)) + '號'
                    else:
                        return no_brackets_text[:idx - 1:-1] + str(random.randrange(fr + 1, to, 2)) + '號'
                except NameError:
                    return text

    def _get_more_info(self) -> List[str]:
        output = []
        handles_before = self.driver.window_handles
        self.wait.until(lambda driver: len(handles_before) != len(self.driver.window_handles))
        self.driver.switch_to.window(self.driver.window_handles[1])
        for css in more_info_css_list:
            try:
                output.append(self.driver.find_element(By.CSS_SELECTOR, css).text)
            except UnexpectedAlertPresentException:
                self.driver.switch_to.alert.accept()
                output.append(self.driver.find_element(By.CSS_SELECTOR, css).text)
            except NoSuchElementException:
                output.append(None)
        self.driver.close()
        self.driver.switch_to.window(self.default_window)
        return output
