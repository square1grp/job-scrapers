# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from w3lib.html import remove_tags
import re
from job.items import JobItem
import json


class PearsonfrankSpider(scrapy.Spider):
    name = 'pearsonfrank'
    domain = 'https://www.pearsonfrank.com/'

    def __init__(self):
        self.translator = Translator()

    def start_requests(self):
        yield scrapy.Request(url=self.domain+'search?query=&industry%5B0%5D=', callback=self.parse_jobs_page)

    def parse_jobs_page(self, response):
        job_links = response.xpath(
            '//div[@class="top-pagination"]/following-sibling::div[contains(@class, "item")]//h2/a/@href').extract()

        for job_link in job_links:
            yield scrapy.Request(job_link, callback=self.parse_single_job_page)

        next_page_url = response.xpath(
            '//div[@class="top-pagination"]/ul[@class="pagination"]/li[last()]/a/@href').extract_first()

        if next_page_url:
            yield scrapy.Request(next_page_url, callback=self.parse_jobs_page)

    def parse_single_job_page(self, response):
        try:
            json_text = response.xpath(
                '//header/following-sibling::script[@type="application/ld+json"]/text()').extract_first().strip()
            json_data = json.loads(json_text)

            title = self.get_title(response)
            translated_title = self.get_translated_title(title)
            need_translation = "true" if translated_title is None else "false"

            raw_description = self.get_raw_description(response)
            description = self.get_description(raw_description)
            translated_description = self.get_translated_description(
                response, description)

            job_url = response.url
            source_url = self.domain
            source_name = 'PEARSON FRANK'

            [country, state, city] = self.get_location(response)

            translated_raw_industry = raw_industry = None

            date_posted = self.get_date_posted(response)

            raw_rate = self.get_raw_rate(response)
            translated_raw_rate = self.get_translated_raw_rate(raw_rate)
            rate_type = self.get_rate_type(raw_rate)
            rate_value = None
            rate_values = self.get_rate_values(raw_rate)

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
                country=country,
                currency=json_data['baseSalary']['currency'],
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
        except:
            pass

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
        return response.xpath('//div[@class="job-description"]/div[@class="padding-top-job"]').extract_first()

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

    def get_raw_rate(self, response):
        try:
            return response.xpath('//span[@itemprop="benefits"]/text()').extract_first().strip()
        except:
            return None

    def get_translated_raw_rate(self, raw_rate):
        try:
            return self.translator.translate(raw_rate).text
        except:
            return None

    def get_rate_type(self, raw_rate):
        if raw_rate is None or raw_rate == 'N/A':
            return 3

        if 'per annum' in raw_rate:
            return 2

        if 'per month' in raw_rate:
            return 6

        if 'per hour' in raw_rate:
            return 1

        if 'per day' in raw_rate:
            return 4

        return 3

    def get_rate_values(self, raw_rate):
        try:
            rate_values = re.findall("\d+", raw_rate)[:2]

            return rate_values
        except:
            return None

    def get_location(self, response):
        loc_txt = ''.join(response.xpath(
            '//span[contains(text(), "Location:")]/following-sibling::span//text()').extract()).strip()
        loc_arr = loc_txt.split(', ')

        if not len(loc_arr):
            return [None, None, None]

        if len(loc_arr) == 1:
            loc_arr += [None, None]

        if len(loc_arr) == 2:
            loc_arr = [loc_arr[0], None, loc_arr[1]]

        return loc_arr

    def get_date_posted(self, response):
        try:
            return response.xpath('//span[@itemprop="datePosted"]/text()').extract_first().strip()
        except:
            return None
