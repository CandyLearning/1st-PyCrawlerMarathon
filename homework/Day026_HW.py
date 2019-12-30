# -*- coding: utf-8 -*-
import scrapy
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pprint import pprint
class PttcrawlerSpider(scrapy.Spider):
    name = 'PTTCrawler'
    allowed_domains = ['www.ptt.cc']
    start_urls = ['https://www.ptt.cc/bbs/TaiwanDrama/index.html']
#     cookies = {'over18': '1'}

    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        soup = BeautifulSoup(response.text, 'html5lib')
        for d in soup.find_all(class_ = 'title'):
            print('標題:', d.text.replace('\t', '').replace('\n', ''))
            try:
                r = BeautifulSoup(requests.get('https://www.ptt.cc' + d.find('a')['href']).text, 'html5lib')
                metalines = r.find_all(class_ = 'article-metaline')
                print('作者:', metalines[0].find(class_ = 'article-meta-value').text)
                print('時間:', metalines[2].find(class_ = 'article-meta-value').text)
                print()
            except:
                print()
                continue    