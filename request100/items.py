# Define here the models for your scraped items
#
# See documentation in:
# https://docs.scrapy.org/en/latest/topics/items.html

import scrapy


class Request100Item(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    pass

class Movie(scrapy.Item):
    title = scrapy.Field()
    moviePage = scrapy.Field()
    movieDownloadPage = scrapy.Field()
    subtitleDownloadPage = scrapy.Field()
    movieDownloadLink = scrapy.Field()
    subtitleDownloadLink = scrapy.Field()
