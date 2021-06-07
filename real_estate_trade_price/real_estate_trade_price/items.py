# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html
import datetime

import scrapy


class RealEstateTradePriceItem(scrapy.Item):
    district = scrapy.Field()
    address = scrapy.Field()
    trade_date = scrapy.Field()
    total_price = scrapy.Field()
    unit_price = scrapy.Field()
    unit_price_include_park = scrapy.Field()
    building_area = scrapy.Field()
    land_area = scrapy.Field()
    building_type = scrapy.Field()
    building_age = scrapy.Field()
    floor = scrapy.Field()
    total_floor = scrapy.Field()
    trade_include_park = scrapy.Field()
    remark = scrapy.Field()
    first_trade = scrapy.Field()
    building_layout = scrapy.Field()
    have_guard = scrapy.Field()
    land_type = scrapy.Field()
    building_material = scrapy.Field()
    longitude = scrapy.Field()
    latitude = scrapy.Field()
    exit_id = scrapy.Field()
    distance_to_mrt = scrapy.Field()

    def get_check_sql(self):
        return f"""
            select * from trade_price_raw where district = '{self['district']}' and trade_date = '{self['trade_date']}'
            and total_price = {self['total_price']} and building_area like {self['building_area']:g}
            and floor {'is null' if self['floor'] is None else '= ' + str(self['floor'])}
            """

    @staticmethod
    def get_insert_sql():
        return f"""
            insert into trade_price_raw(district, address, trade_date, total_price, unit_price, unit_price_include_park, 
            building_area, land_area, building_type, building_age, floor, total_floor, trade_include_park, remark, 
            first_trade, building_layout, have_guard, land_type, building_material, longitude, latitude, exit_id,
            distance_to_mrt, create_time)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """

    def get_values(self):
        return (self['district'], self['address'], self['trade_date'], self['total_price'], self['unit_price'],
                self['unit_price_include_park'], self['building_area'], self['land_area'], self['building_type'],
                self['building_age'], self['floor'], self['total_floor'], self['trade_include_park'], self['remark'],
                self['first_trade'], self['building_layout'], self['have_guard'], self['land_type'], self['building_material'],
                self['longitude'], self['latitude'], self['exit_id'], self['distance_to_mrt'], datetime.datetime.now())
