# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html


# useful for handling different item types with a single interface
import math

import MySQLdb
import MySQLdb.cursors
from twisted.enterprise import adbapi


class RealEstateTradePricePipeline:
    def __init__(self, pool):
        self.pool = pool

    @classmethod
    def from_crawler(cls, crawler):
        params = dict(
            host=crawler.settings['MYSQL_HOST'],
            db=crawler.settings['MYSQL_DATABASE'],
            user=crawler.settings['MYSQL_USERNAME'],
            passwd=crawler.settings['MYSQL_PASSWORD'],
            charset='utf8',
            cursorclass=MySQLdb.cursors.DictCursor,
            use_unicode=True,
        )

        pool = adbapi.ConnectionPool('MySQLdb', **params)
        return cls(pool)

    def process_item(self, item, spider):
        self.pool.runInteraction(self._do_insert, item)
        return item

    @staticmethod
    def _do_insert(cursor, item):
        cursor.execute(item.get_check_sql())
        if cursor.fetchone() is None:
            cursor.execute(item.get_insert_sql(), item.get_values())
