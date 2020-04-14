# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from w3lib.html import remove_tags
import re
from job.items import JobItem


class NigelfrankSpider(scrapy.Spider):
    name = 'nigelfrank'
    search_url = 'https://www.nigelfrank.com/search?page={}&query=&location%5B0%5D=3611&type=Permanent%3BContract'

    def __init__(self):
        self.translator = Translator()

    def start_requests(self):
        page_idx = 1

        yield scrapy.Request(
            url=self.search_url.format(page_idx),
            callback=self.parse_search_results_page,
            meta=dict(page_idx=page_idx))

    def parse_search_results_page(self, response):
        job_links = response.xpath(
            '//div[@class="item new"]/p/a[contains(@class, "btn-view")]/@href').extract()

        if job_links:
            for job_link in job_links:
                yield scrapy.Request(job_link, callback=self.parse_single_job_page)

            page_idx = response.meta['page_idx'] + 1

            yield scrapy.Request(
                url=self.search_url.format(page_idx),
                callback=self.parse_search_results_page,
                meta=dict(page_idx=page_idx))

    def parse_single_job_page(self, response):
        title = self.get_title(response)
        translated_title = self.get_translated_title(title)
        need_translation = "true" if translated_title is None else "false"

        raw_description = self.get_raw_description(response)
        description = self.get_description(raw_description)
        translated_description = self.get_translated_description(
            response, description)

        job_url = response.url
        source_url = 'https://www.nigelfrank.com/'
        source_name = 'Nigel Frank'

        [city, state] = self.get_location(response)

        raw_industry = self.get_raw_industry(response)
        translated_raw_industry = self.get_translated_raw_industry(
            raw_industry)

        date_posted = self.get_date_posted(response)

        raw_rate = self.get_raw_rate(response)
        translated_raw_rate = self.get_translated_raw_rate(raw_rate)
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
            country='Sweden',
            currency='SEK' if 'SEK' in raw_rate else 'EUR',
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
            return response.xpath('//div[@class="page-header"]/h1/text()').extract_first()
        except:
            return None

    def get_translated_title(self, title):
        try:
            return self.translator.translate(title).text
        except:
            return None

    def get_raw_description(self, response):
        try:
            return response.xpath('//div[@class="job-description"]/div[@class="padding-top-job"]').extract_first()
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
                    '//div[@class="job-description"]/div[@class="padding-top-job"]//text()').extract()
                t_lines = [self.translator.translate(
                    line).text for line in lines]

                return '\n'.join(t_lines)
            except:
                return None

    def get_location(self, response):
        try:
            city = ''.join(response.xpath(
                '//span[@class="heading" and contains(text(), "Location:")]/following-sibling::span//text()').extract()).strip().split(', ')[0]
            return [city, None]
        except:
            return [None, None]

    def get_raw_rate(self, response):
        try:
            raw_rate = ''.join(response.xpath(
                '//span[@class="heading" and contains(text(), "Salary:")]/following-sibling::span//text()').extract()).strip()
            return raw_rate
        except:
            return None

    def get_translated_raw_rate(self, raw_rate):
        try:
            return self.translator.translate(raw_rate).text
        except:
            return None

    def get_rate_type(self, raw_rate):
        if 'per hour' in raw_rate:
            return 1

        if 'per annum' in raw_rate:
            return 2

        if 'per month' in raw_rate:
            return 6

        return 3

    def get_rate_values(self, raw_rate):
        try:
            p_raw_rate_1 = raw_rate.split('month')[0]
            p_raw_rate_1 = p_raw_rate_1.split('annum')[0]
            p_raw_rate_1 = p_raw_rate_1.split('hour')[0]

            rate_values = re.findall("\d+", p_raw_rate_1)[:2]

            return rate_values
        except:
            return None

    def get_raw_industry(self, response):
        try:
            return ''.join(response.xpath('//span[@class="heading" and contains(text(), "Technology:")]/following-sibling::span//text()').extract()).strip()
        except:
            return None

    def get_translated_raw_industry(self, raw_industry):
        try:
            return self.translator.translate(raw_industry).text
        except:
            return None

    def get_date_posted(self, response):
        try:
            return ''.join(response.xpath('//span[@class="heading" and contains(text(), "Date Posted:")]/following-sibling::span//text()').extract()).strip()
        except:
            return None
