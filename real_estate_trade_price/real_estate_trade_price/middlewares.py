# Define here the models for your spider middleware
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/spider-middleware.html
from math import radians, sin, cos, asin, sqrt
from typing import Tuple

import MySQLdb
from requests.utils import requote_uri
from scrapy import signals
from selenium import webdriver

# useful for handling different item types with a single interface
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.wait import WebDriverWait

from real_estate_trade_price import settings


class RealEstateTradePriceSpiderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    def __init__(self):
        self.db = MySQLdb.connect(host=settings.MYSQL_HOST, db='real_estate', user=settings.MYSQL_USERNAME, passwd=settings.MYSQL_PASSWORD)
        self.cursor = self.db.cursor()
        self.cursor.execute('select exit_id, longitude, latitude from taipei_mrt_exit')
        self.mrt_exit_coordinate = self.cursor.fetchall()

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, or item objects.
        for item in result:
            lon, lat = self._trans_addr_to_coord(item['district'] + item['address'])
            item['longitude'], item['latitude'] = lon, lat
            item['exit_id'], item['distance_to_mrt'] = self._get_dist_to_mrt(lon, lat)
            yield item

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Request or item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)

    @staticmethod
    def _trans_addr_to_coord(addr: str) -> Tuple[float, float]:
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument('--headless')
        chrome_options.add_argument('--disable-gpu')
        driver = webdriver.Chrome(chrome_options=chrome_options)
        url = requote_uri(f"https://map.tgos.tw/TGOSimpleViewer/Web/Map/TGOSimpleViewer_Map.aspx?addr={addr}")
        driver.get(url)

        try:
            WebDriverWait(driver, 30, 0.01).until(lambda url_change: driver.current_url != url)
            info = driver.current_url
            building_lon = float(info[info.index('CX=') + 3:info.index('CY=') - 1])
            building_lat = float(info[info.index('CY=') + 3:info.index('L=') - 1])
        except (TimeoutException, ValueError):
            driver.close()
            return -1.0, -1.0

        driver.close()
        return building_lon, building_lat

    def _get_dist_to_mrt(self, lon: float, lat: float) -> Tuple[float, float]:
        shortest_distance = float('inf')
        shortest_exit_id = -1
        for row in self.mrt_exit_coordinate:
            lon1, lat1, lon2, lat2 = map(radians, [lon, lat, row[1], row[2]])
            a = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
            c = 2 * asin(sqrt(a))
            r = 6371
            distance = c * r * 1000
            if distance < shortest_distance:
                shortest_exit_id = row[0]
                shortest_distance = distance
        return shortest_exit_id, shortest_distance


class RealEstateTradePriceDownloaderMiddleware:
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)
