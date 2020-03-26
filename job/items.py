# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class JobItem(scrapy.Item):
    title = scrapy.Field()
    translated_title = scrapy.Field()
    need_translation = scrapy.Field()
    raw_description = scrapy.Field()
    description = scrapy.Field()
    translated_description = scrapy.Field()
    job_url = scrapy.Field()
    source_url = scrapy.Field()
    source_name = scrapy.Field()
    city = scrapy.Field()
    state = scrapy.Field()
    country = scrapy.Field()
    currency = scrapy.Field()
    rate_type = scrapy.Field()
    rate_value = scrapy.Field()
    raw_rate = scrapy.Field()
    translated_raw_rate = scrapy.Field()
    raw_industry = scrapy.Field()
    translated_raw_industry = scrapy.Field()
    industry = scrapy.Field()
    date_posted = scrapy.Field()
