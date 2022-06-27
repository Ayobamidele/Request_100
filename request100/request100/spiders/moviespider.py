import scrapy
import urllib.parse
import emoji
import requests
import time
import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen


class StagaSpider(scrapy.Spider):
    name = "staga"
    search_text = "ip"
    safe_string = urllib.parse.quote_plus(search_text)
    start_urls = [f'https://www.stagatv.com/?s={search_text}']

    def parse(self, response):
        for movies in response.css('div.bx'):
            movie = {
                'title': movies.css('h2.entry-title ::text').get(),
                'link': movies.css('a').attrib['href'],
            }
            if 'series' in movie['link'] or 'subtitle' in movie['link']:
                pass
            else:
                yield response.follow(movie['link'],callback=self.parse_product, meta={'title': movie['title']})

    def parse_product(self, response):
        product_url = {
            "Url": response.xpath('//div[@class="dl-item"]//a[@class="linkselector"]/@href'),
            "Referrer": response.xpath("//link[@rel='canonical']/@href").get(),
            "Title": response.meta['title'],
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
                'Page Referrer': product_url['Referrer'],
                'content':arrange_links([ x.get() for x in product_url['Url'] ]),
            }
        download_link = data['content'].get('movie')
        if len([ x.get() for x in product_url['Url'] ]) > 0:
            yield response.follow(download_link,callback=self.parse_download, meta={'data': data})
        else:
            yield data
        

    def parse_download(self, response):
        data = response.meta['data']
        token = response.css('#om_dl::attr(data-file)').get()
        download_request = requests.post(data['content']['movie'], data={'token': token,'api': "1",'dataType': "JSON"},)
        # time.sleep(10)
        try:
            download_link = download_request.json()
            data['download_link'] = download_link['file']
        except Exception as e:
            download_link = download_request.text
            data['download_link'] = "Use referrer."
        yield data
    