import scrapy
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from pathlib import Path
from pprint import pprint
from ..items import PTTArticleItem

class PttcrawlerSpider(scrapy.Spider):
    name = 'PTTCrawler'
    def __init__(self, board ='Gossiping', start = 19454, end = 39109):
        self.cookies = {'over18': '1'}
        self.host = 'https://www.ptt.cc'
         # 偽裝瀏覽器
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36(KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}
        self.board = board
       
        # 起始頁數
        self.start = start
        # 結尾頁數
        self.end = end
        # 目前爬取的頁面 index
        self.now_index = start - 1 # 未爬取
        # 要爬取的目標網址
        self.start_urls = [] 
        for i in range(end - start + 1):
            # 取得的文章頁數
            index = self.start + i
            url = 'https://www.ptt.cc/bbs/{}/index{}.html'.format(board, str(index))
            self.start_urls.append(url)
        super().__init__()

    # 對目標網址送出請求
    def start_requests(self):
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.parse, cookies=self.cookies, headers = self.headers)
    # 取得文章列表中的清單主體
    def parse(self, response):
        self.now_index = self.now_index + 1
        if response.status != 200:
            self.log('Error - {} is not available to access'.format(response.url))
            return
        self.log('Processing index {}'.format(self.now_index))
        soup = BeautifulSoup(response.text)
        main_list = soup.find('div', class_='bbs-screen')

        # 依序檢查文章列表中的 tag, 遇到分隔線就結束，忽略這之後的文章
        for div in main_list.findChildren('div', recursive=False):
            class_name = div.attrs['class']

            # 遇到分隔線要處理的情況
            if class_name and 'r-list-sep' in class_name:
                self.log('Reach the last article')
                break

            # 遇到目標文章
            if class_name and 'r-ent' in class_name:
                div_title = div.find('div', class_='title')
                a_title = div_title.find('a', href=True)
                # 如果文章已經被刪除則跳過
                if not a_title or not a_title.has_attr('href'):
                    continue
                article_URL = urljoin(self.host, a_title['href'])
                article_title = a_title.text
#                 self.log('Parse article {}'.format(article_title))
                yield scrapy.Request(url=article_URL,
                                     callback=self.parse_article, # parse_article function
                                     cookies=self.cookies, headers = self.headers)
    
# response取得文章內容，整理取得目標資料，送入Item Pipeline
    def parse_article(self, response):
        # 假設網頁回應不是 200 OK 的話, 我們視為傳送請求失敗
        if response.status != 200:
            self.log('Error - {} is not available to access'.format(response.url))
            return
    
        # 將網頁回應的 HTML 傳入 BeautifulSoup 解析器, 方便我們根據標籤 (tag) 資訊去過濾尋找
        soup = BeautifulSoup(response.text)
    
        # 取得文章內容主體
        main_content = soup.find(id='main-content')
    
    # 假如文章有屬性資料 (meta), 我們在從屬性的區塊中爬出作者 (author), 文章標題 (title), 發文日期 (date)
        metas = main_content.select('div.article-metaline')
        try:
            if metas:
                if metas[0].select('span.article-meta-value')[0]:
                    author = metas[0].select('span.article-meta-value')[0].string
                if metas[1].select('span.article-meta-value')[0]:
                    title = metas[1].select('span.article-meta-value')[0].string
                if metas[2].select('span.article-meta-value')[0]:
                    date = metas[2].select('span.article-meta-value')[0].string

            # 從 main_content 中移除 meta 資訊（author, title, date 與其他看板資訊）
            #
            # .extract() 方法可以參考官方文件
            #  - https://www.crummy.com/software/BeautifulSoup/bs4/doc/#extract
                for m in metas:
                    m.extract()
                for m in main_content.select('div.article-metaline-right'):
                    m.extract()
        except:
            title = ''
            date = ''
            author = ''
        
        # 取得"留言"區主體
        pushes = main_content.find_all('div', class_='push')
        for p in pushes:
            p.extract()
    
        # 假如文章中有包含「※ 發信站: 批踢踢實業坊(ptt.cc), 來自: xxx.xxx.xxx.xxx」的樣式
        # 透過 regular expression 取得 IP
        # 因為字串中包含特殊符號跟中文, 這邊建議使用 unicode 的型式 u'...'
        try:
            ip = main_content.find(text=re.compile(u'※ 發信站:'))
            ip = re.search('[0-9]*\.[0-9]*\.[0-9]*\.[0-9]*', ip).group()
        except Exception as e:
            ip = ''
    
        # 移除文章主體中 '※ 發信站:', '◆ From:', 空行及多餘空白 (※ = u'\u203b', ◆ = u'\u25c6')
        # 保留英數字, 中文及中文標點, 網址, 部分特殊符號
        #
        # 透過 .stripped_strings 的方式可以快速移除多餘空白並取出文字, 可參考官方文件 
        #  - https://www.crummy.com/software/BeautifulSoup/bs4/doc/#strings-and-stripped-strings
        # 過濾
        filtered = []
        for v in main_content.stripped_strings:
        # 假如字串開頭不是特殊符號或不是以 '--' 開頭的, 我們都保留其文字
            if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--']:
                filtered.append(v)
        
        # 去掉最後的發文網址
        del filtered[-1]
        # 定義一些特殊符號與全形符號的過濾器
        expr = re.compile(u'[^一-龥。；，：“”（）、？《》\s\w:/-_.?~%()]')
        for i in range(len(filtered)):
    #         將特殊符號與全形符號替換成''
    # re.sub(pattern, replace_str, string, replace_count) replace_count為替換個數
            filtered[i] = re.sub(expr, '', filtered[i])
        
    # 移除空字串, 組合過濾後的文字即為文章本文 (content)
        filtered = [i for i in filtered if i] # if i : 將空的內容過濾掉(移除空字串) -
        content = ' '.join(filtered) # 將所有內容所組成的 List (也就是 filtered)拼回一個字串，用空白連接
    
    
         # 處理留言區
        # p 計算推文數量
        # b 計算噓文數量
        # n 計算箭頭數量
        p, b, n = 0, 0, 0
        messages = []
        for push in pushes:
            try:
                # 假如留言段落沒有 push-tag 就跳過
                if not push.find('span', 'push-tag'):
                    continue
        
                # 過濾額外空白與換行符號
                # push_tag 判斷是推文, 箭頭還是噓文
                # push_userid 判斷留言的人是誰
                # push_content 判斷留言內容
                # push_ipdatetime 判斷留言日期時間
                push_tag = push.find('span', 'push-tag').string.strip(' \t\n\r')
                push_userid = push.find('span', 'push-userid').string.strip(' \t\n\r')
                push_content = push.find('span', 'push-content').strings
                push_content = ' '.join(push_content)[1:].strip(' \t\n\r')
                push_ipdatetime = push.find('span', 'push-ipdatetime').string.strip(' \t\n\r')
            except:
                continue
            
            # 整理打包留言的資訊, 並統計推噓文數量
            messages.append({
                'push_tag': push_tag,
                'push_userid': push_userid,
                'push_content': push_content,
                'push_ipdatetime': push_ipdatetime})
            if push_tag == u'推':
                p += 1
            elif push_tag == u'噓':
                b += 1
            else:
                n += 1
        # 統計推噓文
        # count 為推噓文相抵看這篇文章推文還是噓文比較多
        # all 為總共留言數量 
        message_count = {'all': p+b+n, 'count': p-b, 'push': p, 'boo': b, 'neutral': n}
        
        # 整理文章資訊
        data = PTTArticleItem()
        article_id = str(Path(urlparse(response.url).path).stem)
        data['url'] = response.url
        data['article_id'] = article_id
        data['article_author'] = author
        data['article_title'] = title
        data['article_date'] = date
        data['article_content'] = content
        data['ip'] = ip
        data['message_count'] = message_count
        data['messages'] = messages
        yield data