# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from job.items import JobItem
from w3lib.html import remove_tags


class CvkeskusSpider(scrapy.Spider):
    name = 'cvkeskus'
    domain = 'https://www.cvkeskus.ee'
    history = []

    def __init__(self):
        self.translator = Translator()

    def start_requests(self):
        yield scrapy.Request('https://www.cvkeskus.ee/toopakkumised-kategooriates', callback=self.parse_page_categories)

    def parse_page_categories(self, response):
        cat_link_tags = response.xpath(
            '//div[@class="f_jobs_table hidden-xs-down"]//a[@class="main_job_link"]')

        for cat_link_tag in cat_link_tags:
            cat_link = cat_link_tag.xpath('./@href').extract_first()
            cat_name = cat_link_tag.xpath('./text()').extract_first()

            cat_link = '{}{}'.format(
                '' if 'http' in cat_link else self.domain, cat_link)

            yield scrapy.Request(cat_link, callback=self.parse_page_search_results,
                                 meta=dict(page_idx=0, org_url=cat_link, cat_name=cat_name))

    def parse_page_search_results(self, response):
        job_link_tags = response.xpath('//tr[@class="f_job_row2"]')

        if job_link_tags:
            org_url = response.meta['org_url']
            page_idx = response.meta['page_idx']+1
            cat_name = response.meta['cat_name']

            for job_link_tag in job_link_tags:
                job_link = job_link_tag.xpath(
                    './td[contains(@class, "hidden-xs-down main-column")]/a[@class="f_job_title main_job_link limited-lines"]/@href').extract_first()

                raw_rate = rate_values = None
                salaray_tag = job_link_tag.xpath(
                    './td[contains(@class, "hidden-xs-down main-column")]/span[contains(@class, "f_job_salary")]')
                if salaray_tag:
                    raw_rate = ''.join(
                        salaray_tag.xpath('.//text()').extract()).strip()
                    start_value = salaray_tag.xpath(
                        './@data-salary-from').extract_first()
                    to_value = salaray_tag.xpath(
                        './@data-salary-to').extract_first()

                    rate_values = [start_value, to_value] if start_value != to_value else [
                        start_value]

                job_link = '{}{}'.format(
                    '' if 'http' in job_link else self.domain, job_link)

                yield scrapy.Request(job_link, callback=self.parse_page_single_job,
                                     meta=dict(raw_rate=raw_rate, rate_values=rate_values, cat_name=cat_name))

            yield scrapy.Request('{}?start={}'.format(org_url, page_idx*25), callback=self.parse_page_search_results,
                                 meta=dict(page_idx=page_idx, org_url=org_url, cat_name=cat_name))

    def parse_page_single_job(self, response):
        image_container = response.xpath(
            '//div[contains(@class, "job-offer jobad-view-image")]').extract()

        if image_container:
            return

        title = self.get_title(response)
        translated_title = self.get_translated_title(title)
        need_translation = "true" if translated_title is None else "false"

        raw_description = self.get_raw_description(response)
        description = self.get_description(raw_description)
        translated_description = self.get_translated_description(
            response, description)

        job_url = response.url
        source_url = 'https://www.cvkeskus.ee'
        source_name = 'CVKESKUS.ee'

        [city, state] = self.get_location(response)

        raw_industry = response.meta['cat_name']
        translated_raw_industry = self.get_translated_raw_industry(
            raw_industry)

        date_posted = self.get_date_posted(response)

        raw_rate = response.meta['raw_rate']
        translated_raw_rate = self.get_translated_raw_rate(raw_rate)
        rate_type = self.get_rate_type(raw_rate)
        rate_values = response.meta['rate_values']
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
            country='Estonia',
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

    def get_title(self, response):
        title_tag = response.xpath('//h1[@id="main-job-title"]')

        if not title_tag:
            title_tag = response.xpath('//span[@id="main-job-title"]')

        return title_tag.xpath('./text()').extract_first()

    def get_translated_title(self, title):
        try:
            return self.translator.translate(title).text
        except:
            return None

    def get_raw_description(self, response):
        return response.xpath('//div[@class="main-lang-block"]').extract_first()

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
        loc = ''.join(response.xpath(
            '//div[@class="job-details-table"]//i[@class="fa fa-map-marker"]/parent::div[@class="jobdetails_key"]/following-sibling::div[@class="jobdetails_value"]/text()').extract())
        loc = loc.split(', ')

        if len(loc) == 1:
            return [loc[0].strip(), None]
        elif len(loc) > 1:
            return [loc[0].strip(), loc[1].strip()]
        else:
            return [None, None]

    def get_translated_raw_rate(self, raw_rate):
        try:
            return self.translator.translate(raw_rate).text
        except:
            return None

    def get_rate_type(self, raw_rate):
        if raw_rate:
            if 'kuus' in raw_rate:
                return 6

            if 'tunnis' in raw_rate:
                return 1

            if 'aastas' in raw_rate:
                return 2

        return 3

    def get_translated_raw_industry(self, raw_industry):
        try:
            return self.translator.translate(raw_industry).text
        except:
            return None

    def get_date_posted(self, response):
        try:
            org_date = ''.join(response.xpath(
                '//div[@class="job-details-table"]//i[@class="fa fa-calendar-check-o"]/parent::div[@class="jobdetails_key"]/following-sibling::div[@class="jobdetails_value"]/text()').extract())

            return org_date.strip()
        except:
            return None
