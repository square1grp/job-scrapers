# -*- coding: utf-8 -*-
import scrapy
from job.items import JobItem
from googletrans import Translator


class NeuvooSpider(scrapy.Spider):
    name = 'neuvoo'
    allowed_domains = ['neuvoo.it']
    start_urls = ['http://neuvoo.it/']
    link_history = []

    def __init__(self):
        self.translator = Translator()

    def start_requests(self):
        yield scrapy.Request('https://neuvoo.it/stipendio/', callback=self.parse)

    def parse(self, response):
        links = response.xpath(
            '//a[@class="card--infoList--li"]/@href').extract()

        for link in links:
            link = 'https://neuvoo.it%s' % link if 'http' not in link else link

            if link not in self.link_history:
                self.link_history.append(link)

                yield scrapy.Request(link, callback=self.parse_single)

    def get_rate_type(self, type_txt):
        if type_txt == 'Mese':
            return 6

        if type_txt == 'Anno':
            return 2

        if type_txt == 'Settimana':
            return 5

        if type_txt == 'Ora':
            return 1

        return 3

    def get_rate_value(self, value_txt):
        try:
            return float(''.join(value_txt.split(' ')[:-1]))
        except:
            return None

    def parse_single(self, response):
        try:
            title = response.xpath(
                '//div[@class="card--title"]/text()').extract_first().strip()
            title = title.replace(': Stipendio', '')

            try:
                translated_title = self.translator.translate(title).text
            except:
                translated_title = title

            raw_description = description = translated_description = None

            job_url = response.url
            source_url = 'https://neuvoo.it'
            source_name = 'neuvoo'
            city = state = None
            country = 'Italy'
            currency = 'EUR'

            type_txt = response.xpath(
                '//div[contains(@class, "card--btnGroup--btn--isSelected")]/text()').extract_first().strip()
            type_txt = type_txt[:1].upper() + type_txt[1:]

            rate_type = self.get_rate_type(type_txt)

            rate_value = response.xpath(
                '//div[@id="matchedJob-stats"]//div[@class="card--stats--head"]/div[1]/text()').extract_first().strip()
            rate_value = self.get_rate_value(rate_value)

            med_raw_rate = response.xpath(
                '//div[@class="card--stats--rightChart"]/div[@class="card--stats--medianLabel"]/div/text()').extract()
            med_raw_rate = ' : '.join([txt.strip() for txt in med_raw_rate])

            low_raw_rate = response.xpath(
                '//div[@class="card--stats--rightChart"]//div[@class="card--stats--lowLabel"]/div/text()').extract()
            low_raw_rate = ' : '.join([txt.strip() for txt in low_raw_rate])

            high_raw_rate = response.xpath(
                '//div[@class="card--stats--rightChart"]//div[@class="card--stats--highLabel"]/div/text()').extract()
            high_raw_rate = ' : '.join([txt.strip() for txt in high_raw_rate])

            raw_rate = ', '.join([low_raw_rate, med_raw_rate, high_raw_rate])
            try:
                translated_raw_rate = self.translator.translate(raw_rate).text
            except:
                translated_raw_rate = raw_rate

            raw_industry = translated_raw_industry = None

            date_posted = None

            min_value = response.xpath(
                '//div[@class="card--stats--rightChart"]//div[@class="card--stats--lowLabel"]/div[2]/text()').extract_first().strip()
            min_value = self.get_rate_value(min_value)

            max_value = response.xpath(
                '//div[@class="card--stats--rightChart"]//div[@class="card--stats--highLabel"]/div[2]/text()').extract_first().strip()
            max_value = self.get_rate_value(max_value)

            for _rate_value in [rate_value, min_value, max_value]:
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
                    rate_value=_rate_value,
                    raw_rate=raw_rate,
                    translated_raw_rate=translated_raw_rate,
                    raw_industry=raw_industry,
                    translated_raw_industry=translated_raw_industry,
                    date_posted=date_posted
                )

                yield item

            for region in response.xpath('//form[@class="l-container"]/div[@class="l-card card"][3]/a[@class="card--progressBar--row"]'):
                state = region.xpath(
                    './/div[@class="card--progressBar--text"]/text()').extract_first().strip()

                rate_value = region.xpath(
                    './/div[contains(@class, "card--progressBar--number")]/text()').extract_first().strip()

                try:
                    rate_value = self.get_rate_value(rate_value)
                except:
                    rate_value = None

                if rate_value:
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

            link = response.xpath(
                '//form[@class="l-container"]/div[@class="l-card card card--progressBar--row__dark"]/div/@data-src'
            ).extract_first().replace('\n', '').replace('\t', '').replace(' ', '')

            link = 'https://neuvoo.it%s' % link if 'http' not in link else link

            if link not in self.link_history:
                self.link_history.append(link)

                yield scrapy.Request(link, callback=self.parse_ajax)
        except:
            pass

    def parse_ajax(self, response):
        links = response.xpath(
            '//a[contains(@class, "card--progressBar--row")]/@href').extract()

        for link in links:
            link = 'https://neuvoo.it%s' % link if 'http' not in link else link

            if link not in self.link_history:
                self.link_history.append(link)

                yield scrapy.Request(link, callback=self.parse_single)
