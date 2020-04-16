# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from w3lib.html import remove_tags
import re
from job.items import JobItem


class PraceSpider(scrapy.Spider):
    name = 'prace'
    domain = 'https://www.prace.cz/'
    branches = [
        'Administrativa',
        'Auto - moto',
        'Cestovní ruch a ubytování',
        'Doprava a zásobování',
        'Finance a ekonomika',
        'Gastronomie a pohostinství',
        'Chemie a potravinářství',
        'Informatika',
        'Kultura, umění a tvůrčí práce',
        'Marketing, média a reklama',
        'Ostatní',
        'Ostraha a bezpečnost',
        'Personalistika a HR',
        'Školství a vzdělávání',
        'Prodej a obchod',
        'Řemeslné a manuální práce',
        'Služby',
        'Státní zaměstnanci',
        'Stavebnictví a reality',
        'Technika, elektrotechnika a energetika',
        'Telekomunikace',
        'Tisk, vydavatelství a polygrafie',
        'Výroba, průmysl a provoz',
        'Zákaznický servis',
        'Zdravotnictví, farmacie a sociální péče',
        'Zemědělství, lesnictví a ekologie',
    ]

    def __init__(self):
        self.translator = Translator()

    def start_requests(self):
        for branch in self.branches:
            url = 'https://www.prace.cz/hledat/?searchForm[profs]=%s' % branch

            yield scrapy.Request(
                url,
                callback=self.parse_single_branch_page,
                meta=dict(branch=branch, page_idx=1))

    def parse_single_branch_page(self, response):
        org_url = response.meta['org_url'] if 'org_url' in response.meta else response.url
        page_idx = response.meta['page_idx'] + 1
        branch = response.meta['branch']

        job_li_items = response.xpath(
            '//h3/a[contains(@href, "https://www.prace.cz/nabidka/")]/ancestor::li[@class="search-result__advert"]')

        if job_li_items:
            for job_li_item in job_li_items:
                job_link = job_li_item.xpath(
                    './/h3/a[contains(@href, "https://www.prace.cz/nabidka/")]/@href').extract_first()
                city = job_li_item.xpath(
                    './/div[contains(@class, "search-result__advert__box__item--location")]/strong/text()').extract_first()

                yield scrapy.Request(job_link, callback=self.parse_single_job_page, meta=dict(branch=branch, city=city))

            url = org_url+'?page=%s' % page_idx
            yield scrapy.Request(
                url,
                callback=self.parse_single_branch_page,
                meta=dict(org_url=org_url, branch=branch, page_idx=page_idx))

    def parse_single_job_page(self, response):
        if self.domain not in response.url:
            return

        try:
            title = self.get_title(response)
            translated_title = self.get_translated_title(title)
            need_translation = "true" if translated_title is None else "false"

            raw_description = self.get_raw_description(response)
            description = self.get_description(raw_description)
            translated_description = self.get_translated_description(
                response, description)

            job_url = response.url
            source_url = self.domain
            source_name = 'prace.cz'

            city = response.meta['city'].strip()

            raw_industry = response.meta['branch']
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
                state=None,
                country='Czech',
                currency='CZK',
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
            return response.xpath('//h1[@class="advert__title"]/text()').extract_first()
        except:
            return None

    def get_translated_title(self, title):
        try:
            return self.translator.translate(title).text
        except:
            return None

    def get_raw_description(self, response):
        return response.xpath('//div[@class="advert__richtext"]').extract_first()

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
                    '//div[@class="advert__richtext"]//text()').extract()
                t_lines = [self.translator.translate(
                    line).text for line in lines]

                return '\n'.join(t_lines)
            except:
                return None

    def get_raw_rate(self, response):
        try:
            return response.xpath('//h3[@class="advert__salary"]/text()').extract_first().replace(u'\xa0', u' ')
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

        if 'rok' in raw_rate:
            return 2

        if 'hodina' in raw_rate:
            return 1

        if 'jednor' in raw_rate:
            return 3

        return 6

    def get_rate_values(self, raw_rate):
        try:
            rate_values = re.findall("\d+", raw_rate.replace(' ', ''))

            return rate_values
        except:
            return None

    def get_translated_raw_industry(self, raw_industry):
        try:
            return self.translator.translate(raw_industry).text
        except:
            return None

    def get_date_posted(self, response):
        return None
