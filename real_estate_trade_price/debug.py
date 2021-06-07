from scrapy.cmdline import execute

if __name__ == '__main__':
    execute(f"scrapy crawl get_tp_buildings_and_land -a start_year=107 -a start_month=1 -a end_year=107 -a end_month=12".split())
