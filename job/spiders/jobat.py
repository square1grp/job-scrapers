# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from w3lib.html import remove_tags
from job.items import JobItem
import pdb


class JobatSpider(scrapy.Spider):
    name = 'jobat'

    def __init__(self):
        self.translator = Translator()

    def start_requests(self):
        url = 'https://www.jobat.be/nl/jobs/results?joblanguage=1,2'

        yield scrapy.Request(url, callback=self.parse_search_result_page, meta=dict(pageIdx=1))

    def parse_search_result_page(self, response):
        job_links = response.xpath(
            '//ul[@class="jobCard-searchResult"]/li/a[@class="jobCard-link"]/@href').extract()

        if len(job_links):
            for job_link in job_links:
                job_link = 'https://www.jobat.be' + job_link

                yield scrapy.Request(job_link, callback=self.parse_single_job_page)

            pageIdx = response.meta['pageIdx'] + 1
            url = 'https://www.jobat.be/nl/jobs/results?joblanguage=1,2&pagenum=%s' % pageIdx

            yield scrapy.Request(url, callback=self.parse_search_result_page, meta=dict(pageIdx=pageIdx))

    def get_title(self, response):
        return response.xpath('//h1[@class="jobCard-title"]/text()').extract_first().strip()

    def get_translated_title(self, title):
        try:
            return self.translator.translate(title).text
        except:
            return None

    def get_raw_description_tags(self, response):
        try:
            return response.xpath('//div[contains(@itemprop, "description")]').extract()
        except:
            return []

    def get_raw_description_lines(self, response):
        try:
            return response.xpath('//div[contains(@itemprop, "description")]//text()').extract()
        except:
            return []

    def get_raw_description(self, raw_description_tags, raw_description_lines):
        try:
            raw_description = ''.join(
                [str(html_tag.encode('utf8').strip()) for html_tag in raw_description_tags])

            if not len(raw_description_tags) and len(raw_description_lines):
                raw_description = '\n'.join(raw_description_lines)

            return raw_description
        except:
            return None

    def get_description(self, raw_description):
        return remove_tags(raw_description) if raw_description else ''

    def get_translated_description(self, description, raw_description_lines):
        try:
            return self.translator.translate(
                description).text
        except:
            if len(raw_description_lines):
                try:
                    return self.translator.translate('\n'.join(raw_description_lines)).text
                except:
                    return None
            else:
                return None

    def get_state(self, response):
        return None

    def get_city(self, response):
        try:
            return response.xpath('//li[@class="jobCard-location"]/text()').extract_first()
        except:
            return None

    def get_date_posted(self, response):
        try:
            return response.xpath('//meta[@itemprop="datePosted"]/@content').extract_first()
        except:
            return None

    def get_raw_industry(self, response):
        try:
            return response.xpath('//meta[@itemprop="industry"]/@content').extract_first()
        except:
            return None

    def get_translated_raw_industry(self, raw_industry):
        try:
            return self.translator.translate(raw_industry).text
        except:
            return None

    def get_rate_type(self, response):
        rate_type = response.xpath(
            '//meta[@itemprop="unitText"]/@content').extract_first()
        if rate_type == 'MONTH':
            return 6

        if rate_type == 'YEAR':
            return 2

        if rate_type == 'HOUR':
            return 1

        return 3

    def get_currency(self, response):
        return 'EUR'

    def get_raw_rate(self, response):
        try:
            texts = [text.strip() for text in response.xpath(
                '//span[@itemprop="baseSalary"]/li[contains(@class, "salary")]/div/span//text()').extract()]

            return ' '.join(texts)
        except:
            return None

    def get_translated_raw_rate(self, raw_rate):
        try:
            return self.translator.translate(raw_rate).text
        except:
            return None

    def get_rate_values(self, response):
        minValue = response.xpath(
            '//meta[@itemprop="minValue"]/@content').extract_first()
        maxValue = response.xpath(
            '//meta[@itemprop="maxValue"]/@content').extract_first()

        if minValue and maxValue:
            return [minValue, maxValue]

        return []

    def parse_single_job_page(self, response):
        title = self.get_title(response)
        translated_title = self.get_translated_title(title)

        raw_description_tags = self.get_raw_description_tags(response)
        raw_description_lines = self.get_raw_description_lines(response)
        raw_description = self.get_raw_description(
            raw_description_tags, raw_description_lines)
        description = self.get_description(raw_description)
        translated_description = self.get_translated_description(
            description, raw_description_lines)

        job_url = response.url
        source_url = 'https://jobat.be/'
        source_name = 'Jobat'
        state = self.get_state(response)
        city = self.get_city(response)
        country = 'Belgium'
        currency = self.get_currency(response)

        raw_rate = self.get_raw_rate(response)
        translated_raw_rate = self.get_translated_raw_rate(raw_rate)
        rate_values = self.get_rate_values(response)
        rate_type = self.get_rate_type(response)

        raw_industry = self.get_raw_industry(response)
        translated_raw_industry = self.get_translated_raw_industry(
            raw_industry)
        date_posted = self.get_date_posted(response)

        item = JobItem(
            title=title,
            translated_title=translated_title,
            raw_description=raw_description,
            description=description,
            translated_description=translated_description,
            job_url=job_url,
            source_url=source_url,
            source_name=source_name,
            city=city,
            state=state,
            country=country,
            currency=currency,
            rate_type=rate_type,
            rate_value=None,
            raw_rate=raw_rate,
            translated_raw_rate=translated_raw_rate,
            raw_industry=raw_industry,
            translated_raw_industry=translated_raw_industry,
            date_posted=date_posted
        )

        if len(rate_values):
            for rate_value in rate_values:
                item['rate_value'] = rate_value

                yield item
        else:
            yield item
