# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from w3lib.html import remove_tags
from job.items import JobItem
import re
from datetime import datetime, timedelta


class ComputrabajoSpider(scrapy.Spider):
    name = 'computrabajo'
    start_urls = ['http://www.computrabajo.com/']

    def __init__(self):
        self.translator = Translator()

        self.currencies = {
            'https://www.computrabajo.com.mx': 'MXN',
            'https://www.computrabajo.com.co': 'COP',
        }

    def start_requests(self):
        websites = [
            dict(domain='https://www.computrabajo.com.mx/', country='Mexico'),
            dict(domain='https://www.computrabajo.com.co/', country='Colombia'),
        ]

        for website in websites:
            yield scrapy.Request(
                website['domain'] + 'ofertas-de-trabajo/',
                callback=self.parse_job_search_page,
                meta=dict(pageIdx=1, domain=website['domain'], country=website['country']))

    def parse_job_search_page(self, response):
        job_links = response.xpath(
            '//div[@id="p_ofertas"]//div[contains(@class, "bRS bClick")]//a[@class="js-o-link"]/@href').extract()

        if len(job_links):
            meta_data = dict(
                pageIdx=response.meta['pageIdx']+1,
                domain=response.meta['domain'],
                country=response.meta['country']
            )

            for job_link in job_links:
                job_link = response.meta['domain']+job_link

                yield scrapy.Request(job_link, callback=self.parse_single_job_page, meta=meta_data)

            url = '%sofertas-de-trabajo/?p=%s' % (
                meta_data['domain'], meta_data['pageIdx'])
            yield scrapy.Request(url, callback=self.parse_job_search_page, meta=meta_data)

    def get_title(self, response):
        return response.xpath('//h1[@class="m0"]/text()').extract_first().strip()

    def get_translated_title(self, title):
        try:
            return self.translator.translate(title).text
        except:
            return None

    def get_raw_description_tags(self, response):
        return response.xpath('//article[contains(@class, "fl")]//ul[contains(@class, "p0 m0")]/*').extract()

    def get_raw_description_lines(self, response):
        return response.xpath('//article[contains(@class, "fl")]//ul[contains(@class, "p0 m0")]//text()').extract()

    def get_raw_description(self, raw_description_tags, raw_description_lines):
        raw_description = ''.join(
            [str(html_tag.encode('utf8').strip()) for html_tag in raw_description_tags])

        if not len(raw_description_tags) and len(raw_description_lines):
            raw_description = '\n'.join(raw_description_lines)

        return raw_description

    def get_description(self, raw_description):
        return remove_tags(
            raw_description) if raw_description else ''

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
        return response.xpath('//ol[@class="breadcrumb"]/li[2]/a/text()').extract_first()

    def get_city(self, response):
        return response.xpath('//ol[@class="breadcrumb"]/li[3]/a/text()').extract_first()

    def get_raw_rate(self, response):
        try:
            return response.xpath('//p[contains(text(), "Salario")]/../p[2]/text()').extract_first().strip()
        except:
            return None

    def get_translated_raw_rate(self, raw_rate):
        try:
            return self.translator.translate(raw_rate).text
        except:
            return None

    def get_rate_value(self, raw_rate):
        rate_value = re.findall(
            "\d+\.\d+", raw_rate.replace('.', '').replace(',', '.'))
        return rate_value[0]

    def get_rate_type(self, raw_rate):
        if raw_rate:
            if 'Mensual' in raw_rate:
                return 6

        return 3

    def get_raw_industry(self, response):
        try:
            return response.xpath('//a[@id="urlverofertas"]/text()').extract_first().strip()
        except:
            return None

    def get_translated_raw_industry(self, raw_industry):
        try:
            return self.translator.translate(raw_industry).text
        except:
            return None

    def get_date_posted(self, response):
        date_posted = response.xpath(
            '//p[contains(@class, "fc80 mt5")]/text()').extract_first().strip()

        if 'hoy' in date_posted.lower():
            return datetime.today().strftime('%b. %d')
        elif 'ayer' in date_posted.lower():
            return (datetime.today()-timedelta(days=1)
                    ).strftime('%b. %d')
        else:
            date_posted = date_posted.split(' ')[-2:]
            date_posted[1] = date_posted[1][0].upper() + date_posted[1][1:]
            date_posted = ' '.join(date_posted)

            try:
                return self.translator.translate(date_posted).text
            except:
                return None

    def parse_single_job_page(self, response):
        try:
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
            source_url = response.meta['domain']
            source_name = 'CompuTrabajo'
            state = self.get_state(response)
            city = self.get_city(response)
            country = response.meta['country']

            domain = source_url[:-1] if source_url[-1] == '/' else source_url
            currency = self.currencies[domain]

            raw_rate = self.get_raw_rate(response)
            translated_raw_rate = rate_value = None
            if raw_rate:
                translated_raw_rate = self.get_translated_raw_rate(
                    raw_rate)
                rate_value = self.get_rate_value(raw_rate)

            rate_type = self.get_rate_type(raw_rate)

            raw_industry = self.get_raw_industry(response)
            translated_raw_industry = self.get_translated_raw_industry(
                raw_industry) if raw_industry else None

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
