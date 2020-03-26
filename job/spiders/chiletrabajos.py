# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from job.items import JobItem
import json
import pdb
import re


class ChiletrabajosSpider(scrapy.Spider):
    name = 'chiletrabajos'

    def __init__(self):
        self.translator = Translator()

        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3952.0 Safari/537.36'
        }

    def start_requests(self):
        url = 'https://www.chiletrabajos.cl/encuentra-un-empleo'
        pageIdx = 1

        yield scrapy.Request(url, headers=self.headers, callback=self.parse_search_results, meta=dict(org_url=url, pageIdx=pageIdx))

    def parse_search_results(self, response):
        job_links = response.xpath(
            '//div[@class!="relacionadas"]/div[contains(@class, "job-item")]//h2[@class="title"]/a/@href').extract()

        if len(job_links):
            for job_link in job_links:
                yield scrapy.Request(job_link, headers=self.headers, callback=self.parse_single_job_page)

            url = response.meta['org_url'] + \
                ('/%s' % (response.meta['pageIdx'] * 30))

            yield scrapy.Request(
                url, headers=self.headers,
                callback=self.parse_search_results,
                meta=dict(
                    org_url=response.meta['org_url'],
                    pageIdx=response.meta['pageIdx'] + 1))

    def get_translated_title(self, title):
        try:
            return self.translator.translate(title).text
        except:
            return None

    def get_translated_description(self, description):
        try:
            return self.translator.translate(
                description).text
        except:
            return None

    def get_translated_raw_industry(self, raw_industry):
        try:
            return self.translator.translate(raw_industry).text
        except:
            return None

    def get_rate_type(self, rate_type):
        if rate_type == 'MONTH':
            return 6

        if rate_type == 'YEAR':
            return 2

        if rate_type == 'HOUR':
            return 1

        return 3

    def get_raw_rate(self, response):
        try:
            return response.xpath('//td[text()="Salario"]/../td[2]/div/text()').extract_first().strip()
        except:
            return None

    def get_translated_raw_rate(self, raw_rate):
        try:
            return self.translator.translate(raw_rate).text
        except:
            return None

    def get_rate_value(self, raw_rate):
        try:
            rate_value = re.findall("\d+", raw_rate.replace('.', ''))

            return rate_value[0]
        except:
            return None

    def convert_json_text(self, json_text):
        return json_text.replace('{\n', '{').replace('}\n', '}').replace(',\n', ',').replace('"\n', '"').replace('\r', '\\r').replace('\n', '\\n').replace('\t', '')

    def get_recovered_text(self, text):
        return text.replace('\\r', '\r').replace('\\n', '\n')

    def parse_single_job_page(self, response):
        try:
            json_text = response.xpath(
                '//script[@type="application/ld+json"]/text()').extract_first().strip().replace('\\', ' ')

            json_text = self.convert_json_text(json_text)
            json_data = json.loads(json_text)

            title = json_data['title']
            translated_title = self.get_translated_title(title)
            need_translation = "true" if translated_title is None else "false"

            description = self.get_recovered_text(json_data['description'])
            raw_description = description.replace(
                '\n', '<br/>').replace('\r', '')

            translated_description = self.get_translated_description(
                description)

            job_url = response.url
            source_url = 'https://www.chiletrabajos.cl/'
            source_name = 'chiletrabajos'

            address = json_data['jobLocation']['address']
            state = address['addressRegion']
            city = address['addressLocality']
            country = 'Chile'
            currency = json_data['baseSalary']['currency']

            raw_rate = self.get_raw_rate(response)
            translated_raw_rate = self.get_translated_raw_rate(raw_rate)
            rate_value = self.get_rate_value(raw_rate)
            rate_type = self.get_rate_type(
                json_data['baseSalary']['value']['unitText'])

            raw_industry = json_data['industry']
            translated_raw_industry = self.get_translated_raw_industry(
                raw_industry)
            date_posted = json_data['datePosted'].split()[0]

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
                currency=currency,
                rate_type=rate_type,
                rate_value=rate_value,
                raw_rate=raw_rate,
                translated_raw_rate=translated_raw_rate,
                raw_industry=raw_industry,
                translated_raw_industry=translated_raw_industry,
                date_posted=date_posted
            )

            yield item
        except:
            pass
