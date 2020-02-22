import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

def main():
    board = 'Gossiping'
    process = CrawlerProcess(get_project_settings())
    # 取得半年內的貼文: 2019/7/1(index19454)~2020/2/11(index39109)
    process.crawl('PTTCrawler', board = board, start = 19454, end = 39109)
    process.start() 


if __name__ == '__main__':
    main()
