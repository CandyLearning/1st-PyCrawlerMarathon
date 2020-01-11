import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from twisted.internet import reactor, defer

# ReactorNotRestartable 
# https://stackoverflow.com/questions/39946632/reactornotrestartable-error-in-while-loop-with-scrapy

def main():
    target_board = ['Gossiping'] # 'TaiwanDrama'
    
    process = CrawlerProcess(get_project_settings())
    for board in target_board:
        process.crawl('PTTCrawler', board=board)
        
#     process.start() 要放在 for 迴圈的外面，
    
    process.start() # start() 只可以被呼叫一次，這裡只會產生一個.json檔，包含兩個版的內容


if __name__ == '__main__':
    main()
