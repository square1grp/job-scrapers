# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from job.items import JobItem
from w3lib.html import remove_tags
import re


class PlacementindiaSpider(scrapy.Spider):
    name = 'placementindia'
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    }

    def __init__(self):
        self.translator = Translator()

    def start_requests(self):
        yield scrapy.Request('https://www.placementindia.com/jobs-by-industry.htm', headers=self.headers, callback=self.parse_page_industries)

    def parse_page_industries(self, response):
        industry_links = response.xpath(
            '//section/div/ul/li/a[contains(@href, "/job-search/")]/@href').extract()

        for industry_link in industry_links:
            yield scrapy.Request('{}?search_type=htm_page&pageno=1&id2=refine_search&promotional_page=n'.format(industry_link),
                                 headers=self.headers, callback=self.parse_page_industry,
                                 meta=dict(org_url=industry_link, page_idx=1))

    def parse_page_industry(self, response):
        job_links = response.xpath(
            '//ul[@id="jobs_results"]/li/@data-url').extract()

        if job_links:
            for job_link in job_links:
                yield scrapy.Request(job_link, headers=self.headers, callback=self.parse_page_single_job)

            industry_link = response.meta['org_url']
            page_idx = response.meta['page_idx'] + 1

            yield scrapy.Request('{}?search_type=htm_page&pageno={}&id2=refine_search&promotional_page=n'.format(industry_link, page_idx),
                                 headers=self.headers, callback=self.parse_page_industry,
                                 meta=dict(org_url=industry_link, page_idx=page_idx))

    def parse_page_single_job(self, response):
        if not response.xpath('//section[@id="left_content"]'):
            return

        translated_title = title = self.get_title(response)
        need_translation = "true" if translated_title is None else "false"

        raw_description = self.get_raw_description(response)
        translated_description = description = self.get_description(
            raw_description)

        job_url = response.url
        source_url = 'https://www.placementindia.com/'
        source_name = 'PLACEMENTINDIA'

        [city, state] = self.get_location(response)

        translated_raw_industry = raw_industry = self.get_raw_industry(
            response)

        date_posted = self.get_date_posted(response)

        translated_raw_rate = raw_rate = self.get_raw_rate(response)
        rate_type = self.get_rate_type(raw_rate)
        rate_values = self.get_rate_values(raw_rate)
        rate_value = None

        item = JobItem(
            title=title,
            translated_title=translated_title,
            need_translation=need_translation,
            raw_description=raw_description,
            description=description,
            translated_description=translated_description,
            job_url=job_url,
            source_url=source_url,
            source_name=source_name,
            city=city,
            state=state,
            country='India',
            currency='INR',
            rate_type=rate_type,
            rate_value=rate_value,
            raw_rate=raw_rate,
            translated_raw_rate=translated_raw_rate,
            raw_industry=raw_industry,
            translated_raw_industry=translated_raw_industry,
            date_posted=date_posted
        )

        if rate_values:
            for rate_value in rate_values:
                item['rate_value'] = rate_value

                yield item
        else:
            yield item

    def get_title(self, response):
        try:
            return response.xpath('//p[@itemprop="title"]/text()').extract_first()
        except:
            return None

    def get_translated_title(self, title):
        try:
            return self.translator.translate(title).text
        except:
            return None

    def get_raw_description(self, response):
        try:
            return response.xpath('//div[@itemprop="description"]').extract_first()
        except:
            return None

    def get_description(self, raw_description):
        return remove_tags(
            raw_description) if raw_description else None

    def get_translated_description(self, response, description):
        try:
            return self.translator.translate(
                description).text
        except:
            try:
                lines = response.xpath(
                    '//div[@class="main-lang-block"]//text()').extract()
                t_lines = [self.translator.translate(
                    line).text for line in lines]

                return '\n'.join(t_lines)
            except:
                return None

    def get_location(self, response):
        try:
            city = response.xpath(
                '//span[@itemprop="addressLocality"]/a/text()').extract_first()
            return [city, None]
        except:
            return [None, None]

    def get_raw_rate(self, response):
        try:
            raw_rate = response.xpath(
                '//img[contains(@src, "icon-salary")]/following-sibling::span/text()').extract_first()
            if 'Rs' in raw_rate:
                raw_rate = 'Rs ' + raw_rate.replace('Rs', '').strip()
            return raw_rate
        except:
            return None

    def get_translated_raw_rate(self, raw_rate):
        try:
            return self.translator.translate(raw_rate).text
        except:
            return None

    def get_rate_type(self, raw_rate):
        try:
            return 2 if 'p.a.' in raw_rate else 3
        except:
            return 3

    def get_rate_values(self, raw_rate):
        try:
            rate_values = re.findall("\d+", raw_rate.replace(',', ''))

            return rate_values
        except:
            return None

    def get_raw_industry(self, response):
        try:
            return response.xpath('//p[@itemprop="industry"]/a/text()').extract_first()
        except:
            return None

    def get_translated_raw_industry(self, raw_industry):
        try:
            return self.translator.translate(raw_industry).text
        except:
            return None

    def get_date_posted(self, response):
        try:
            return response.xpath('//span[@itemprop="datePosted"]/text()').extract_first().strip()
        except:
            return None
