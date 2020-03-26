# from __future__ import unicode_literals
import scrapy
import json
from jobs.items import JobItem
from w3lib.html import remove_tags
from googletrans import Translator
from lxml import etree


class IntermediairSpider(scrapy.Spider):

    name = 'intermediair'

    init_url = 'https://cookiewall.vnumediaonline.nl/intermediair?destination=/&referrer='

    def __init__(self):
        self.translator = Translator()

    def get_headers(self):
        return {
            'accept': 'application/json, text/plain, */*',
            'cookie': 'policyv3=accepted; _gcl_au=1.1.39393010.1580375304; __gads=ID=3cc4e53b28c4b44b:T=1580375305:S=ALNI_MZc25DSgdT-kxonoyap7G5enjZrKw; _ga=GA1.2.792254636.1580375304; _gid=GA1.2.1983198255.1580375311; __aaxsc=0; kppid_managed=NMjqbwzf; cX_S=k60inumpdje0639i; cX_P=k60inums35oxrtfr; cX_G=cx%3A393617ibno6ei3sy7poxql02oi%3Agh5fjamhpzkv; _fbp=fb.1.1580375328472.1878470124; __Host-latestLocation=; __Host-latestDistance=city; aasd=2%7C1580375309954; _gat_UA-334005-1=1; _dc_gtm_UA-334005-1=1; lastConsentChange=1580375720753; _tty=7033600091164184003; cstp=1',
            'referer': 'None',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
        }

    def start_requests(self):
        headers = {
            'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
            'accept-encoding': 'gzip, deflate, br',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://cookiewall.vnumediaonline.nl',
            'referer': 'https://cookiewall.vnumediaonline.nl/intermediair?destination=/&referrer=',
            'upgrade-insecure-requests': '1',
            'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'
        }

        formdata = {
            'form[destination]': '/',
            'form[referrer]': '',
            'form[save]': ''
        }

        yield scrapy.FormRequest(self.init_url, formdata=formdata, headers=headers, method="post", callback=self.start_parsing)

    def start_parsing(self, response):
        '''
        target_urls = [
            'https://www.intermediair.nl/vacature/34440471/hoofd-polikliniek-oogheelkunde',
            'https://www.intermediair.nl/vacature/34561260/servicemedewerker'
        ]

        for target_url in target_urls:
            yield scrapy.Request(target_url, headers=self.get_headers(), callback=self.parse_job_detail_page)
        '''

        target_url = 'https://www.intermediair.nl/vacature/zoeken.json?query=&location=&distance=city&page=1&limit=100&sort=date'
        yield scrapy.Request(target_url, headers=self.get_headers(), callback=self.parse_job_listing_page, meta=dict(page=1))

    def parse_job_listing_page(self, response):
        json_data = json.loads(response.body)

        page = response.meta['page']
        max_page = json_data['result']['pagination']['pages']

        jobs = json_data['result']['jobs']

        for job in jobs:
            job_detailUrl = 'https://www.intermediair.nl%s' % job['detailUrl']

            yield scrapy.Request(job_detailUrl, headers=self.get_headers(), callback=self.parse_job_detail_page)

        if max_page > page:
            page += 1
            target_url = 'https://www.intermediair.nl/vacature/zoeken.json?query=&location=&distance=city&page=%s&limit=100&sort=date' % page

            yield scrapy.Request(target_url, headers=self.get_headers(), callback=self.parse_job_listing_page, meta=dict(page=page))

    def get_raw_rate(self, workingHours):
        if workingHours['min'] == workingHours['max']:
            return '%s hours per week' % workingHours['min']

        return '%s ~ %s hours per week' % (workingHours['min'], workingHours['max'])

    def get_rate_type(self, contract_type, raw_rate):
        if 'bruto per maand' in raw_rate:
            return 6

        if contract_type == 'Vast':
            return 2

        return 3

    def parse_job_detail_page(self, response):
        try:
            try:
                title = response.xpath(
                    '//h1[@itemprop="title"]/text()').extract_first().strip()
            except:
                title = response.xpath(
                    '//meta[@itemprop="title"]/@content').extract_first()

            raw_description_tags = response.xpath(
                '//section[@role="job.description"]//div[@itemprop="description"]/*').extract()
            raw_description_lines = response.xpath(
                '//section[@role="job.description"]//div[@itemprop="description"]//text()').extract()

            raw_description = ''.join(
                [str(html_tag.encode('utf8').strip()) for html_tag in raw_description_tags])

            if not len(raw_description_tags) and len(raw_description_lines):
                raw_description = '\n'.join(raw_description_lines)

            if not raw_description:
                raw_description = response.xpath(
                    '//meta[@itemprop="description"]/@content').extract_first()

                raw_description_lines = etree.HTML(
                    raw_description.encode('utf8')).xpath('//text()')

            description = remove_tags(
                raw_description) if raw_description else ''

            job_url = response.xpath(
                '//meta[@itemprop="url"]/@content').extract_first()

            source_url = 'https://www.intermediair.nl'
            source_name = 'Intermediair'
            city = response.xpath(
                '//span[@itemprop="address"]/meta[@itemprop="addressLocality"]/@content').extract_first()
            country = 'Netherlands'

            currency = response.xpath(
                '//meta[@itemprop="currency"]/@content').extract_first()

            rate_value = None
            raw_rate = ''.join([text.strip() for text in response.xpath(
                '//dd[@itemprop="baseSalary"]/text()').extract()])

            contract_type = response.xpath(
                '//a[@data-gtm="job-contract-type"]/@data-slug').extract_first()
            rate_type = self.get_rate_type(contract_type, raw_rate)

            raw_industry = response.xpath(
                '//a[@data-gtm="job-industry"]/text()').extract_first()

            try:
                date_posted = response.xpath(
                    '//time[@itemprop="datePosted"]/@datetime').extract()[-1].split()[0]
            except:
                date_posted = ''

            try:
                translated_title = self.translator.translate(title).text
            except:
                translated_title = title

            try:
                translated_description = self.translator.translate(
                    description).text
            except:
                if len(raw_description_lines):
                    try:
                        translated_description = self.translator.translate('\n'.join(
                            raw_description_lines)).text
                    except:
                        translated_description = description
                else:
                    translated_description = description

            try:
                translated_raw_rate = self.translator.translate(raw_rate).text
            except:
                translated_raw_rate = raw_rate

            try:
                translated_raw_industry = self.translator.translate(
                    raw_industry).text
            except:
                translated_raw_industry = raw_industry

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

            minValue = response.xpath(
                '//meta[@itemprop="minValue"]/@content').extract_first()
            maxValue = response.xpath(
                '//meta[@itemprop="maxValue"]/@content').extract_first()

            if minValue:
                rate_value = float(minValue)
                item['rate_value'] = rate_value

            if rate_value is None:
                item['raw_rate'] = None

            yield item

            if minValue and maxValue:
                if minValue != maxValue:
                    rate_value = float(maxValue)
                    item['rate_value'] = rate_value

                    if rate_value is None:
                        item['raw_rate'] = None

                    yield item
        except:
            print('====== %s ' % response.url)
