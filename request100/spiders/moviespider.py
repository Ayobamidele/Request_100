import scrapy
import urllib.parse
import emoji
import requests
import time
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import re
import os
import glob
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from pyshadow.main import Shadow
import chromedriver_autoinstaller

API_KEY = '931c3d83e351fc155d5d2ceca17a10ed'

# chromedriver_autoinstaller.install()

class Movie(scrapy.Item):
    title = scrapy.Field()
    moviePage = scrapy.Field()
    movieDownloadPage = scrapy.Field()
    subtitleDownloadPage = scrapy.Field()
    movieDownloadLink = scrapy.Field()
    subtitleDownloadLink = scrapy.Field()


def get_scraperapi_url(url):

    payload = {'api_key': API_KEY, 'url': url}

    proxy_url = 'http://api.scraperapi.com/?' + urlencode(payload)

    return proxy_url

class StagaSpider(scrapy.Spider):
    name = "staga"
    # search_text = "ip"
    # safe_string = urllib.parse.quote_plus(search_text)
    # start_urls = [f'https://www.stagatv.com/?s={search_text}']

    def __init__(self,search_text='', **kwargs): # The search_text variable will have the input URL.SS
        self.completed_search_links = False
        self.search_links = []
        self.page = 0
        safe_string = urllib.parse.quote_plus(search_text)
        self.start_urls = [f'https://www.stagatv.com/?s={safe_string}']
        super().__init__(**kwargs)


    def parse(self, response):
        for movies in response.css('div.bx'):
            movie = {
                'title': movies.css('h2.entry-title ::text').get(),
                'link': movies.css('a').attrib['href'],
                'type': movies.css('i.type ::text').get(),
            }
            if 'series' in movie['link'] or 'subtitle' in movie['link']:
                pass
            # else:
                # yield response.follow(movie['link'],callback=self.parse_product, meta={'title': movie['title']})
                # pass
            else:
                self.search_links.append(movie)
        try:
            next_page = response.css('a.page-numbers.next').attrib['href']
        
            if next_page is not None and self.page < 6:
                yield response.follow(next_page, callback=self.parse)
                self.page+=1
            else:
                self.completed_search_links = True
        except Exception as e:
            next_page = response.css('div.bx')
            self.completed_search_links = True
        if self.completed_search_links:
            # print(self.search_links)
            yield response.follow("https://www.stagatv.com/", callback=self.parse_product2)


    def parse_product2(self, response):    
        for movie in self.search_links:
            yield response.follow(movie['link'], callback=self.parse_product, meta={'title': movie['title'],'type': movie['type']})

    def parse_product(self, response):
        product_url = {
            "Image": response.css('img.entry-image').attrib['src'],
            "Url": response.xpath('//div[@class="dl-item"]//a[@class="linkselector"]/@href'),
            "Referrer": response.xpath("//link[@rel='canonical']/@href").get(),
            "Title": response.meta['title'],
            'Duration': response.css('span[property="duration"]::text').extract_first(),
            "Trailer": response.css('#trailer div.limit iframe').attrib['src'],
            }
        def arrange_links(links):
            arranged_links = dict()
            error_message = dict()
            print(len(links))
            if len(links) > 0:
                for link in links:
                    if link.endswith('srt') or 'subtitle' in link:
                        arranged_links['subtitle'] = link
                    else:
                        arranged_links['movie'] = link
                return arranged_links
            else:
                error_message['successful'] = False
                error_message['message'] = f'Spider{emoji.emojize(":spider:")}  has problems navigating this page {emoji.emojize(":spider_web:")} .'
                return error_message

        data = {
            'Title': product_url['Title'],
            'Trailer': product_url['Trailer'],
            'Page Referrer': product_url['Referrer'],
            'Image': product_url['Image'],
            'Type': response.meta['type'],
            'Duration': product_url['Duration'],
            'content': arrange_links([x.get() for x in product_url['Url']]),
        }
        download_link = data['content'].get('movie')
        if len([x.get() for x in product_url['Url']]) > 0:
            yield response.follow(download_link, callback=self.parse_download, meta={'data': data})
        else:
            pass

    def parse_download(self, response):
        data = response.meta['data']
        url = data['content']['movie']
        token = response.css('#om_dl::attr(data-file)').get()
        download_request = requests.post(
            url, data={'token': token, 'api': "1", 'dataType': "JSON"},)
        try:
            download_link = download_request.json()
            data['download_link'] ="https://stagatvfiles.com" + download_link['file']
        except Exception as e:
            path = "NUL"
            options = Options()
            options.add_experimental_option(
                "prefs", {"safebrowsing.enabled": True, "download.restrictions": 3, "download.default_directory": path, "download.prompt_for_download": False, "safebrowsing.disable_download_protection": True, })
            options.add_argument("--headless")
            driver = webdriver.Chrome(options=options)
            # driver.maximize_window()
            wait = WebDriverWait(driver, 20)
            driver.get(url)
            # https://stagatvfiles.com/videos/file/61f1aaaf36957/Juniper-2021-STAGATV-COM-mp4
            ele = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "button[id='om_dl']")))
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", ele)
            driver.execute_script("arguments[0].click();", ele)
            time.sleep(3)
            # driver.get("c://downloads/")
            # time.sleep(3)
            # //*[@id="om_result"]/div/div/a
            ele2 = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="om_result"]/div/div/a')))
            ele2.get_attribute("href")

            data['download_link'] = "https://stagatvfiles.com" + ele2.get_attribute("href")
            for file in glob.glob(os.getcwd() + "/NUL/*"):
                print('Deleting file:', file)
                os.remove(file)
            driver.quit()

        if 'subtitle' in data['content']:
            yield response.follow(data['content']['subtitle'], callback=self.parse_subtitles, meta={'data': data})
        else:
            yield data

    def parse_subtitles(self, response):
        print(response.url)
        data = response.meta['data']
        url = data['content']['subtitle']
        token = response.css('#om_dl::attr(data-file)').get()
        download_request = requests.post(
            url, data={'token': token, 'api': "1", 'dataType': "JSON"},)
        try:
            download_link = download_request.json()
            data['subtitle_download_link'] = "https://stagatvfiles.com" + download_link['file']
        except Exception as e:
            path = "NUL"
            options = Options()
            options.add_experimental_option(
                "prefs", {"safebrowsing.enabled": True, "download.restrictions": 3, "download.default_directory": path, "download.prompt_for_download": False, "safebrowsing.disable_download_protection": True, })
            options.add_argument("--headless")
            driver = webdriver.Chrome(options=options)
            # driver.maximize_window()
            wait = WebDriverWait(driver, 20)
            driver.get(url)
            # https://stagatvfiles.com/videos/file/61f1aaaf36957/Juniper-2021-STAGATV-COM-mp4
            ele = wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "button[id='om_dl']")))
            driver.execute_script(
                "arguments[0].scrollIntoView(true);", ele)
            driver.execute_script("arguments[0].click();", ele)
            time.sleep(3)
            # driver.get("c://downloads/")
            # time.sleep(3)
            # //*[@id="om_result"]/div/div/a
            ele2 = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//*[@id="om_result"]/div/div/a')))
            ele2.get_attribute("href")

            data['subtitle_download_link'] = "https://stagatvfiles.com" + ele2.get_attribute("href")
            for file in glob.glob(os.getcwd() + "/NUL/*"):
                print('Deleting file:', file)
                os.remove(file)
            driver.quit()
        yield data


class NetSpider(scrapy.Spider):
    name = "net9"

    def __init__(self,search_text='', **kwargs): # The search_text variable will have the input URL.SSy
        self.page = 1
        self.search_completed = False
        self.allowed_domains = ["thenetnaija.net", "https://www.thenetnaija.net"]
        self.safe_string = urllib.parse.quote_plus(search_text)
        self.start_urls = [f'https://www.thenetnaija.net/search?folder=videos&t={self.safe_string}']
        self.movies = []
        self.series = []
        self.visit_pages = 5
        self.success = 0
        self.links_used = 0
        self.count = 0
        self.path = "NUL"
        self.options = Options()
        self.options.add_experimental_option(
            "prefs", {"safebrowsing.enabled": True, "download.restrictions": 3, "download.default_directory": self.path, "download.prompt_for_download": False, "safebrowsing.disable_download_protection": True, })
        self.options.add_argument("--headless")
        self.driver = webdriver.Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 5)
        super().__init__(**kwargs)

    def parse(self, response):
        for movie in response.css('.sr-one a::attr(href)').extract():
            if "movies" in movie:
                self.movies.append(movie)

        next_page = response.xpath('//a[text()="Next »"]/@href').get()
        
        if next_page is not None and self.page < self.visit_pages:
            yield response.follow(next_page, callback=self.parse)
            self.page += 1
        else:
            self.search_completed = True
        
        if self.search_completed:
            yield response.follow(self.allowed_domains[1], callback=self.parse_data)
    
    def parse_data(self, response):
        # self.search_completed = False if self.success != len(self.movies) else True
        for movie in self.movies:
            self.success += 1
            yield response.follow(movie, callback=self.parse_movie)
        
    def parse_movie(self, response):
        data = {
            "Title": response.css(".page-h1 ::text").get(),
            "Image": response.css(".post-body img ::attr(src)").get(),
            "Description": response.css(".post-body p ::text").get(),
            "Movie Page": response.url,
            "Type": "Movie",
            "Download": {
                    "Movie":{
                            "Page": self.allowed_domains[1] + response.css("div.db-one:nth-child(1) a::attr(href)").get(),
                            },
                    "Subtitle": {
                            "Page": self.allowed_domains[1] + response.css("div.db-one:nth-child(2) a::attr(href)").get(),
                            }
                        },
                }
        """Get Movie Download Link"""
        # path = "NUL"
        # options = Options()
        # options.add_experimental_option(
        #     "prefs", {"safebrowsing.enabled": True, "download.restrictions": 3, "download.default_directory": path, "download.prompt_for_download": False, "safebrowsing.disable_download_protection": True, })
        # options.add_argument("--headless")
        # self.driver = webdriver.Chrome(options=options)
        # wait = WebDriverWait(self.driver, 20)
        self.driver.get(data["Download"]["Movie"]["Page"])
        ele = self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, "#action-buttons > button")))
        self.driver.execute_script(
            "arguments[0].scrollIntoView(true);", ele)
        self.driver.execute_script("arguments[0].click();", ele)
        time.sleep(1)
        ele2 = self.wait.until(EC.presence_of_element_located(
            (By.CSS_SELECTOR, '.download-message a')))
        data['download_link'] = ele2.get_attribute("href")
        for file in glob.glob(os.getcwd() + "/NUL/*"):
            print('Deleting file:', file)
            os.remove(file)

        if data["Download"]["Subtitle"]["Page"]:
            """
                Get Subtitle file for Movie if available.

            """
            # path = "NUL"
            # self.options = Options()
            # options.add_experimental_option(
            #     "prefs", {"safebrowsing.enabled": True, "download.restrictions": 3, "download.default_directory": path, "download.prompt_for_download": False, "safebrowsing.disable_download_protection": True, })
            # options.add_argument("--headless")
            # self.driver = webdriver.Chrome(options=options)
            # wait = WebDriverWait(self.driver, 20)
            self.driver.get(data["Download"]["Subtitle"]["Page"])
            ele = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, "#action-buttons > button")))
            self.driver.execute_script(
                "arguments[0].scrollIntoView(true);", ele)
            self.driver.execute_script("arguments[0].click();", ele)
            time.sleep(1)
            ele2 = self.wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, '.download-message a')))
            data["subtitle_download_link"] = ele2.get_attribute("href")
            for file in glob.glob(os.getcwd() + "/NUL/*"):
                print('Deleting file:', file)
                os.remove(file)
            

        if self.links_used == len(self.movies):
            self.driver.quit()
        yield data

