# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from w3lib.html import remove_tags
from job.items import JobItem
import pdb
import re


class JobsonlineSpider(scrapy.Spider):
    name = 'jobsonline'
    start_urls = ['http://www.jobsonline.be/']

    def __init__(self):
        self.translator = Translator()

    def start_requests(self):
        url = 'https://www.jobsonline.be/vacatures/'

        yield scrapy.Request(url, callback=self.parse_search_result_page, meta=dict(pageIdx=1))

    def parse_search_result_page(self, response):
        job_links = response.xpath(
            '//div[@id="results"]/article/div[@class="jobcontent"]//h2/a/@href').extract()

        if len(job_links):
            for job_link in job_links:
                if 'https' in job_link:
                    continue

                job_link = 'https://www.jobsonline.be' + job_link

                yield scrapy.Request(job_link, callback=self.parse_single_job_page)

            pageIdx = response.meta['pageIdx'] + 1
            url = 'https://www.jobsonline.be/vacatures/pagina-%s/' % pageIdx

            yield scrapy.Request(url, callback=self.parse_search_result_page, meta=dict(pageIdx=pageIdx))

    def get_title(self, response):
        return response.xpath('//div[@id="jobdetail"]/h1/text()').extract_first().strip()

    def get_translated_title(self, title):
        try:
            return self.translator.translate(title).text
        except:
            return None

    def get_raw_description_tags(self, response):
        try:
            return response.xpath('//div[@id="jobdescriptioncontent"]/*').extract()
        except:
            return []

    def get_raw_description_lines(self, response):
        try:
            return response.xpath('//div[@id="jobdescriptioncontent"]//text()').extract()
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
            return response.xpath(
                '//div[@id="jobdetail"]/h2/span[@class="city"]/text()').extract_first().replace('- ', '')
        except:
            return None

    def get_date_posted(self, response):
        return response.xpath('//div[@id="jobdetailproperties"]/h4[text()="Plaatsingsdatum"]/following-sibling::div[@class="jobdetailproperty"][1]/text()').extract_first().strip()

    def get_raw_industry(self, response):
        try:
            return ', '.join([industry_txt.strip() for industry_txt in response.xpath('//div[@id="jobdetailproperties"]/h4[text()="Branche"]/following-sibling::div[@class="jobdetailproperty"][1]/text()').extract()])
        except:
            return None

    def get_translated_raw_industry(self, raw_industry):
        try:
            return self.translator.translate(raw_industry).text
        except:
            return None

    def get_rate_type(self, response):
        txt = ''.join(response.xpath(
            '//div[@id="jobdetailproperties"]/h4[text()="Uren"]/following-sibling::div[@class="jobdetailproperty"][1]//text()').extract())
        if 'uur' in txt:
            return 6

        return 3

    def get_currency(self, response):
        try:
            return response.xpath('//div[@id="jobdetailproperties"]/h4[text()="Salarisindicatie"]/following-sibling::div[@class="jobdetailproperty"][1]/meta[@name="priceCurrency"]/@content').extract_first().strip()
        except:
            return None

    def get_raw_rate(self, response):
        try:
            return response.xpath('//div[@id="jobdetailproperties"]/h4[text()="Salarisindicatie"]/following-sibling::div[@class="jobdetailproperty"][1]/span/text()').extract_first().strip()
        except:
            return None

    def get_translated_raw_rate(self, raw_rate):
        try:
            return self.translator.translate(raw_rate).text
        except:
            return None

    def get_rate_values(self, raw_rate):
        rate_values = re.findall("\d+", raw_rate) if raw_rate else []

        return rate_values

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
        source_url = 'https://www.jobsonline.be/'
        source_name = 'jobsonline'
        state = self.get_state(response)
        city = self.get_city(response)
        country = 'Belgium'
        currency = self.get_currency(response)

        raw_rate = self.get_raw_rate(response)
        translated_raw_rate = self.get_translated_raw_rate(raw_rate)
        rate_values = self.get_rate_values(raw_rate)
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
