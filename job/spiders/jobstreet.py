# -*- coding: utf-8 -*-
import scrapy
from googletrans import Translator
from job.items import JobItem
from w3lib.html import remove_tags
import re
import json
from datetime import datetime, timedelta


class JobstreetSpider(scrapy.Spider):
    name = 'jobstreet'
    domain = 'https://www.jobstreet.com.sg/'
    headers = {
        "user-agent": ' Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'
    }
    payload = "{\"query\":\"{\\r\\n    jobDetail(jobId: \\\"%s\\\",country: \\\"sg\\\",locale: \\\"en\\\") {\\r\\n      id\\r\\n      pageUrl\\r\\n      jobTitleSlug\\r\\n      applyUrls {\\r\\n       mobile\\r\\n       external\\r\\n       loggedInApply\\r\\n      }\\r\\n      isExpired\\r\\n      isConfidential\\r\\n      isClassified\\r\\n      accountNum\\r\\n      advertisementId\\r\\n      subAccount\\r\\n      showMoreJobs\\r\\n      adType\\r\\n      header {\\r\\n        banner {\\r\\n          bannerUrls {\\r\\n            large\\r\\n          }\\r\\n        }\\r\\n        salary {\\r\\n          max\\r\\n          min\\r\\n          type\\r\\n          extraInfo\\r\\n          currency\\r\\n          isVisible\\r\\n          salaryOnDisplay\\r\\n        }\\r\\n        logoUrls {\\r\\n          small\\r\\n          medium\\r\\n          large\\r\\n          normal\\r\\n        }\\r\\n        jobTitle\\r\\n        company {\\r\\n          name\\r\\n          url\\r\\n        }\\r\\n        review {\\r\\n          rating\\r\\n          numberOfReviewer\\r\\n        }\\r\\n        expiration\\r\\n        postedDate\\r\\n        isInternship\\r\\n      }\\r\\n      companyDetail {\\r\\n        companyWebsite\\r\\n        companySnapshot {\\r\\n          avgProcessTime\\r\\n          registrationNo\\r\\n          employmentAgencyPersonnelNumber\\r\\n          employmentAgencyNumber\\r\\n          telephoneNumber\\r\\n          workingHours\\r\\n          website\\r\\n          facebook\\r\\n          size\\r\\n          dressCode\\r\\n          nearbyLocations\\r\\n        }\\r\\n        companyOverview {\\r\\n          html\\r\\n        }\\r\\n        videoUrl\\r\\n        companyPhotos {\\r\\n          caption\\r\\n          url\\r\\n        }\\r\\n      }\\r\\n      jobDetail {\\r\\n        summary,\\r\\n        jobDescription {\\r\\n          html\\r\\n        },\\r\\n        jobRequirement {\\r\\n          careerLevel\\r\\n          yearsOfExperience\\r\\n          qualification\\r\\n          fieldOfStudy\\r\\n          industryValue {\\r\\n            value,\\r\\n            label\\r\\n          }\\r\\n          skills\\r\\n          employmentType\\r\\n          languages\\r\\n          postedDate\\r\\n          closingDate\\r\\n          jobFunctionValue {\\r\\n            code,\\r\\n            name,\\r\\n            children {\\r\\n              code,\\r\\n              name\\r\\n            }\\r\\n          },\\r\\n          benefits\\r\\n        },\\r\\n        whyJoinUs\\r\\n      },\\r\\n      location {\\r\\n        location\\r\\n        locationId\\r\\n        omnitureLocationId\\r\\n      }\\r\\n      sourceCountry\\r\\n    }\\r\\n  }\",\"variables\":{}}"

    def start_requests(self):
        yield scrapy.Request(
            'https://www.jobstreet.com.sg/en/job-search/job-vacancy/1/',
            headers=self.headers,
            callback=self.parse_page_search_results,
            meta=dict(page_idx=1))

    def parse_page_search_results(self, response):
        job_meta_list = response.xpath(
            '//div[@data-automation="jobListing"]/div[@data-search-sol-meta]/@data-search-sol-meta').extract()

        for job_meta in job_meta_list:
            job_meta = json.loads(job_meta)
            job_id = job_meta['jobId'].replace('jobstreet-sg-job-', '')

            yield scrapy.Request(
                'https://xapi.supercharge-srp.co/job-search/graphql?country=sg',
                method='POST',
                headers={'Content-Type': 'application/json'},
                body=self.payload % (job_id),
                callback=self.parse_page_single_job)

        next_btn = response.xpath(
            '//div[@data-automation="pagination"]/div[@class="FYwKg _1chUk_1"]/following-sibling::a')
        if next_btn:
            page_idx = response.meta['page_idx'] + 1

            yield scrapy.Request(
                'https://www.jobstreet.com.sg/en/job-search/job-vacancy/%s/' % page_idx,
                headers=self.headers,
                callback=self.parse_page_search_results,
                meta=dict(page_idx=page_idx))

    def parse_page_single_job(self, response):
        json_data = json.loads(response.body)

        json_data = json_data['data']['jobDetail']

        try:
            translated_title = title = json_data['header']['jobTitle']
        except:
            return

        need_translation = "true" if translated_title is None else "false"

        try:
            raw_description = json_data['jobDetail']['jobDescription']['html']
        except:
            raw_description = None

        translated_description = description = self.get_description(
            raw_description)

        job_url = json_data['pageUrl']
        source_url = 'https://www.jobstreet.com.sg/'
        source_name = 'JobStreet.com'

        try:
            city = json_data['location'][0]['location']
        except:
            city = None
        state = None

        try:
            translated_raw_industry = raw_industry = json_data[
                'jobDetail']['jobRequirement']['industryValue']['label']
        except:
            translated_raw_industry = raw_industry = None

        try:
            date_posted = json_data['jobDetail']['jobRequirement']['postedDate']
            if 'ago' in date_posted:
                try:
                    delta = re.findall("\d+", date_posted)[0]
                except:
                    delta = 1

                if 'minute' in date_posted:
                    date_posted = datetime.now() - timedelta(minutes=int(delta))
                elif 'hour' in date_posted:
                    date_posted = datetime.now() - timedelta(hours=int(delta))

                date_posted = date_posted.strftime('%d-%b-%y')
        except:
            date_posted = None

        try:
            translated_raw_rate = raw_rate = json_data['header']['salary']['salaryOnDisplay']
        except:
            translated_raw_rate = raw_rate = None

        rate_type = self.get_rate_type(raw_rate)
        rate_values = self.get_rate_values(raw_rate)
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
            country='Singapore',
            currency='SGD',
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

    def get_description(self, raw_description):
        return remove_tags(
            raw_description) if raw_description else None

    def get_rate_type(self, raw_rate):
        if raw_rate:
            return 6

        return 3

    def get_rate_values(self, raw_rate):
        try:
            rate_values = re.findall("\d+", raw_rate)

            return rate_values
        except:
            return None
