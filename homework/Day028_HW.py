import scrapy
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# 外部執行Scrapy爬蟲程序，直接執行這個檔案運行程式(用Spyder)
def main():
    target_urls = [
        'https://www.ptt.cc/bbs/Gossiping/M.1559788476.A.074.html',
        'https://www.ptt.cc/bbs/Gossiping/M.1557928779.A.0C1.html'
    ]
#     呼叫 CrawlerProcess就會建立爬蟲流程
#     假如框架中有不同爬蟲可以在這邊給予不同的設定，像是每個請求間delay幾秒
#     或是透過 get_project_setting 取得 myproject 專案的全局設定 (global setting)
    process = CrawlerProcess(get_project_settings()) 

#     每個爬蟲都有一個全局唯一的名稱(eg. PTTCrawler) 可以直接透過這個名稱來決定要開始執行哪個爬蟲
#     後面可以給予爬蟲有定義的參數來改變爬蟲結果(e.g. start_urls 是目標網頁的參數)
#     當爬蟲與其相關對應的元件都修改完成後，就可以直接透過CrawlerProcess在外部給予其他參數: filename='test.json'
    process.crawl('PTTCrawler', start_urls=target_urls, filename='test.json')
    process.start()

if __name__ == '__main__':
    main()
