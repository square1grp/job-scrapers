# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from w3lib.html import remove_tags
import re
from job.items import JobItem


class OpcionempleoSpider(scrapy.Spider):
    name = 'opcionempleo'
    domain = 'https://www.opcionempleo.com'

    def __init__(self):
        self.translator = Translator()

    def url_domain_added(self, url):
        url = self.domain + url if 'http' not in url else url

        return url

    def start_requests(self):
        yield scrapy.Request(self.url_domain_added(''), callback=self.parse_industries_page)

    def parse_industries_page(self, response):
        industry_tags = response.xpath(
            '//div[@id="tab_industry"]//div[@class="column"]/a')

        for industry_tag in industry_tags:
            industry_link = industry_tag.xpath('./@href').extract_first()
            raw_industry = industry_tag.xpath('./text()').extract_first()

            yield scrapy.Request(
                url=self.url_domain_added(industry_link),
                callback=self.parse_single_industry_page,
                meta=dict(raw_industry=raw_industry))

            # return

    def parse_single_industry_page(self, response):
        raw_industry = response.meta['raw_industry']

        job_links = response.xpath(
            '//div[contains(@class, "job display-new-job")]/a[@class="title-company"]/@href').extract()

        for job_link in job_links:
            yield scrapy.Request(
                url=self.url_domain_added(job_link),
                callback=self.parse_single_job_page,
                meta=dict(raw_industry=raw_industry))

            # return

        # '''
        next_page_url = response.xpath(
            '//a/span[contains(text(), ">>")]/parent::a/@href').extract_first()

        if next_page_url:
            yield scrapy.Request(
                url=self.url_domain_added(next_page_url),
                callback=self.parse_single_industry_page,
                meta=dict(raw_industry=raw_industry))
        # '''

    def parse_single_job_page(self, response):
        try:
            title = self.get_title(response)
            translated_title = self.get_translated_title(title)
            need_translation = "true" if translated_title is None else "false"

            raw_description = self.get_raw_description(response)
            description = self.get_description(raw_description)
            translated_description = self.get_translated_description(
                response, description)

            job_url = response.url
            source_url = 'https://www.opcionempleo.com/'
            source_name = 'OPCIONEMPLEO'

            [city, state] = self.get_location(response)

            raw_industry = response.meta['raw_industry']
            translated_raw_industry = self.get_translated_raw_industry(
                raw_industry)

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
                country='Spain',
                currency='EUR',
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
            return response.xpath('//div[@id="job_display"]/div[@class="main_job"]/div/p/a[@class="title_compact"]/text()').extract_first()
        except:
            return None

    def get_translated_title(self, title):
        try:
            return self.translator.translate(title).text
        except:
            return None

    def get_raw_description(self, response):
        return response.xpath('//div[@id="job_display"]/div[@class="main_job"]/div/div[@class="advertise_compact"]').extract_first()

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
                    '//div[@id="job_display"]/div[@class="main_job"]/div/div[@class="advertise_compact"]//text()').extract()
                t_lines = [self.translator.translate(
                    line).text for line in lines]

                return '\n'.join(t_lines)
            except:
                return None

    def get_location(self, response):
        loc = ''.join(response.xpath(
            '//div[@id="job_display"]/div[@class="main_job"]/div//span[@class="icon-lines location"]/parent::div[@class="locations_compact"]/text()').extract())
        loc = loc.split(', ')

        if len(loc) == 1:
            return [loc[0].strip(), None]
        elif len(loc) > 1:
            return [loc[0].strip(), loc[1].strip()]
        else:
            return [None, None]

    def get_raw_rate(self, response):
        try:
            return ''.join(response.xpath('//div[@id="job_display"]/div[@class="main_job"]/div//span[@class="icon-lines salary_icon"]/parent::span[@class="locations_compact"]/text()').extract())
        except:
            return None

    def get_translated_raw_rate(self, raw_rate):
        try:
            return self.translator.translate(raw_rate).text
        except:
            return None

    def get_rate_type(self, raw_rate):
        if raw_rate is None:
            return 3

        if 'mes' in raw_rate:
            return 6

        if 'hora' in raw_rate:
            return 1

        if 'al' in raw_rate:
            return 2

    def get_rate_values(self, raw_rate):
        try:
            rate_values = re.findall(
                "\d+\.\d+" if ',' in raw_rate else "\d+", raw_rate.replace('.', '').replace(',', '.'))

            return rate_values
        except:
            return None

    def get_translated_raw_industry(self, raw_industry):
        try:
            return self.translator.translate(raw_industry).text
        except:
            return None

    def get_date_posted(self, response):
        try:
            org_date = response.xpath('//div[@id="job_display"]/div[@class="main_job"]/div//span[@class="date_compact"]/script/text()').extract_first(
            ).replace('display_string(\' - ', '').replace('\');', '')

            return org_date
        except:
            return None
