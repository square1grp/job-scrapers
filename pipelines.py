# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

from scrapy import signals
from scrapy.exporters import CsvItemExporter


class JobsPipeline(object):
    '''
    def __init__(self):
        self.files = {}

    @classmethod
    def from_crawler(cls, crawler):
        pipeline = cls()
        crawler.signals.connect(pipeline.spider_opened, signals.spider_opened)
        crawler.signals.connect(pipeline.spider_closed, signals.spider_closed)
        return pipeline

    def spider_opened(self, spider):
        file = open('%s_items.csv' % spider.name, 'w+b')
        self.files[spider] = file
        self.exporter = CsvItemExporter(file)
        self.exporter.fields_to_export = ['title',
                                          'translated_title',
                                          'raw_description',
                                          'description',
                                          'translated_description',
                                          'job_url',
                                          'source_url',
                                          'source_name',
                                          'city',
                                          'state',
                                          'country',
                                          'currency',
                                          'rate_type',
                                          'rate_value',
                                          'raw_rate',
                                          'translated_raw_rate',
                                          'raw_industry',
                                          'industry',
                                          'translated_raw_industry',
                                          'date_posted']

        self.exporter.start_exporting()

    def spider_closed(self, spider):
        self.exporter.finish_exporting()
        file = self.files.pop(spider)
        file.close()

    def process_item(self, item, spider):
        self.exporter.export_item(item)

        return item
    '''

    # '''
    def process_item(self, item, spider):

        return item
    # '''
