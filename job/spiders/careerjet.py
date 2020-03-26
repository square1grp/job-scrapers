# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from job.items import JobItem
from w3lib.html import remove_tags
import re


class CareerjetSpider(scrapy.Spider):
    name = 'careerjet'
    domain = 'https://www.careerjet.se'
    scraper_api_url = 'http://api.scraperapi.com/?api_key=********************************&url='

    def __init__(self):
        self.translator = Translator()

    def url_domain_added(self, url):
        url = self.domain + url if 'http' not in url else url

        return self.scraper_api_url + url

    def start_requests(self):
        cat_list = [
            ('/jobb-arkitektur-byggnad-konstruktion.html',
             'Arkitektur - Byggnad - Konstruktion'),
            ('/jobb-bank-finanstjanster.html', 'Bank - Finanstjänster'),
            ('/jobb-bekladnad-mode-textil.html',
             'Beklädnad - Mode -Textil'),
            ('/jobb-bilar-fordon.html', 'Bilar - Fordon'),
            ('/jobb-detaljhandel-grossisthandel.html',
             'Detaljhandel - Grossisthandel'),
            ('/jobb-elektronik-robotics.html', 'Elektronik - Robotics'),
            ('/jobb-fastighet.html', 'Fastighet'),
            ('/jobb-flyg-forsvar.html', 'Flyg - Försvar'),
            ('/jobb-forsakring.html', 'Försäkring'),
            ('/jobb-forsaljning.html', 'Försäljning'),
            ('/jobb-hr-rekrytering.html', 'HR - Rekrytering'),
            ('/jobb-halsovard.html', 'Hälsovård'),
            ('/jobb-informationsteknik-telekommunikation.html',
             'Informationsteknik - Telekommunikation'),
            ('/jobb-ingenjorsarbete.html', 'Ingenjörsarbete'),
            ('/jobb-inkop.html', 'Inköp'),
            ('/jobb-jordbruk-skogsbruk-fiskindustri.html',
             'Jordbruk - Skogsbruk - Fiskindustri'),
            ('/jobb-juridik-skatt.html', 'Juridik - Skatt'),
            ('/jobb-konst-design-underhallning.html',
             'Konst - Design - Underhållning'),
            ('/jobb-konsulation.html', 'Konsulation'),
            ('/jobb-kundservice-call-center.html',
             'Kundservice - Call Center'),
            ('/jobb-kvalitetssakring.html', 'Kvalitetssäkring'),
            ('/jobb-ledning-styrelse.html', 'Ledning - Styrelse'),
            ('/jobb-livsmedelsframstallning.html',
             'Livsmedelsframställning'),
            ('/jobb-maritimt-sjofart-skeppsbyggning.html',
             'Maritimt - Sjöfart - Skeppsbyggning'),
            ('/jobb-marknadsforing-public-relations.html',
             'Marknadsföring - Public relations'),
            ('/jobb-media-annonsering.html', 'Media - Annonsering'),
            ('/jobb-offentlig-sektor.html', 'Offentlig sektor'),
            ('/jobb-olja-gas-gruvdrift.html', 'Olja - Gas - Gruvdrift'),
            ('/jobb-polis-sakerhet.html', 'Polis - Säkerhet'),
            ('/jobb-produktion-underhall.html', 'Produktion - Underhåll'),
            ('/jobb-publicering-tryckning.html', 'Publicering - Tryckning'),
            ('/jobb-redovisning-revision.html', 'Redovisning - Revision'),
            ('/jobb-restaurang-matbetjaning.html',
             'Restaurang - Matbetjäning'),
            ('/jobb-sekreterare-administration.html',
             'Sekreterare - Administration'),
            ('/jobb-skonhet.html', 'Skönhet'),
            ('/jobb-sport-fritid-noje.html', 'Sport - Fritid - Nöje'),
            ('/jobb-stal-metall.html', 'Stål - Metall'),
            ('/jobb-transport-logistik.html', 'Transport - Logistik'),
            ('/jobb-tra-papper-mobler.html', 'Trä - Papper - Möbler'),
            ('/jobb-turism-resa-hotell.html', 'Turism - Resa - Hotell'),
            ('/jobb-utbildning-traning.html', 'Utbildning - Träning'),
            ('/jobb-vetenskap-forskning-utveckling.html',
             'Vetenskap - Forskning - Utveckling'),
            ('/jobb-valgorenhet.html', 'Välgörenhet'),
            ('/jobb-vard-och-omsorg.html', 'Vård och Omsorg'),
            ('/jobb-oversattning-tolk.html', 'Översättning - Tolk')]

        for (cat_link, cat_name) in cat_list:
            yield scrapy.Request(url=self.url_domain_added(cat_link), callback=self.parse_single_cat_page, meta=dict(cat_name=cat_name))

        # yield scrapy.Request(url=self.domain, callback=self.parse_categories)

        # # def parse_categories(self, response):
        #     cat_tags = response.xpath('//div[@id="tab_industry"]//a')

        #     for cat_tag in cat_tags:
        #         cat_link = cat_tag.xpath('./@href').extract_first()
        #         cat_name = cat_tag.xpath('./text()').extract_first()

        #         print((cat_link, cat_name))

        #         # yield scrapy.Request(url=self.url_domain_added(cat_link), callback=self.parse_single_cat_page, meta=dict(cat_name=cat_name))

    def parse_single_cat_page(self, response):
        job_links = response.xpath(
            '//div[contains(@class, "display-new-job")]/a/@href').extract()

        for job_link in job_links:
            yield scrapy.Request(
                url=self.url_domain_added(job_link),
                callback=self.parse_single_job_page,
                meta=dict(cat_name=response.meta['cat_name']))

        next_page_url = response.xpath(
            '//a/span[contains(text(), ">>")]/parent::a/@href').extract_first()

        if next_page_url:
            yield scrapy.Request(
                url=self.url_domain_added(next_page_url),
                callback=self.parse_single_cat_page,
                meta=dict(cat_name=response.meta['cat_name']))

    def get_title(self, response):
        return response.xpath('//div[@id="job_display"]/div[@class="main_job"]/div/h2/a/text()').extract_first()

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
                t_lines = [self.translator.translate(line).text for line in lines]

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
        if raw_rate is None or '/' not in raw_rate:
            return 3

        if '/m' in raw_rate:
            return 6

        if '/h' in raw_rate:
            return 1

        return 2

    def get_rate_values(self, raw_rate):
        try:
            rate_values = re.findall(
                "\d+\.\d+", raw_rate.replace('.', '').replace(',', '.'))

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

    def parse_single_job_page(self, response):
        try:
            title = self.get_title(response)
            translated_title = self.get_translated_title(title)
            need_translation = "true" if translated_title is None else "false"

            raw_description = self.get_raw_description(response)
            description = self.get_description(raw_description)
            translated_description = self.get_translated_description(
                response, description)

            job_url = response.url.replace(self.scraper_api_url, '')
            source_url = 'https://www.careerjet.se'
            source_name = 'careerJET'

            [city, state] = self.get_location(response)

            raw_industry = response.meta['cat_name']
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
                country='Sweden',
                currency='SEK',
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
