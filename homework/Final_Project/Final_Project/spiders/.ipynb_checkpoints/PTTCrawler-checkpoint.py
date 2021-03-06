{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "metadata": {},
   "outputs": [],
   "source": [
    "import scrapy\n",
    "import re\n",
    "from bs4 import BeautifulSoup\n",
    "from urllib.parse import urljoin, urlparse\n",
    "from pathlib import Path\n",
    "from pprint import pprint\n",
    "from ..items import PTTArticleItem\n",
    "\n",
    "class PttcrawlerSpider(scrapy.Spider):\n",
    "    name = 'PTTCrawler'\n",
    "    def __init__(self, board='Gossiping'):\n",
    "        self.cookies = {'over18': '1'}\n",
    "        self.host = 'https://www.ptt.cc'\n",
    "        self.board = board\n",
    "        self.start_urls = 'https://www.ptt.cc/bbs/{}/index.html'.format(board)\n",
    "        super().__init__()\n",
    "\n",
    "    def start_requests(self):\n",
    "        yield scrapy.Request(url=self.start_urls, callback=self.parse, cookies=self.cookies)\n",
    "\n",
    "    def parse(self, response):\n",
    "        # 取得列表中的清單主體\n",
    "        soup = BeautifulSoup(response.text)\n",
    "        main_list = soup.find('div', class_='bbs-screen')\n",
    "\n",
    "        # 依序檢查文章列表中的 tag, 遇到分隔線就結束，忽略這之後的文章\n",
    "        for div in main_list.findChildren('div', recursive=False):\n",
    "            class_name = div.attrs['class']\n",
    "\n",
    "            # 遇到分隔線要處理的情況\n",
    "            if class_name and 'r-list-sep' in class_name:\n",
    "                self.log('Reach the last article')\n",
    "                break\n",
    "\n",
    "            # 遇到目標文章\n",
    "            if class_name and 'r-ent' in class_name:\n",
    "                div_title = div.find('div', class_='title')\n",
    "                a_title = div_title.find('a', href=True)\n",
    "                # 如果文章已經被刪除則跳過\n",
    "                if not a_title or not a_title.has_attr('href'):\n",
    "                    continue\n",
    "                article_URL = urljoin(self.host, a_title['href'])\n",
    "                article_title = a_title.text\n",
    "                self.log('Parse article {}'.format(article_title))\n",
    "#               parse()可返回Request或items，若返回的是Request，items怎麼返回保存？\n",
    "#               Request對象接受一個參數callback，指定這個Request返回的網頁內容解析函數\n",
    "#              所以可以指定parse返回Request，然後指定另一個parse_item方法返回items\n",
    "#                 callback: 用於接收請求後的返回信息，若沒指定，則默認為parse()函數\n",
    "                yield scrapy.Request(url=article_URL,\n",
    "                                     callback=self.parse_article, # parse_article function\n",
    "                                     cookies=self.cookies)\n",
    "# response取得文章內容，整理取得目標資料，送入Item Pipeline\n",
    "    def parse_article(self, response):\n",
    "        headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' / \n",
    "               '(KHTML, like Gecko) Chrome/79.0.3945.130 Safari/537.36'}\n",
    "        response = requests.get(url, cookies={'over18': '1'}, headers = headers, verify = False)\n",
    "    \n",
    "        # 假設網頁回應不是 200 OK 的話, 我們視為傳送請求失敗\n",
    "        if response.status_code != 200:\n",
    "            print('Error - {} is not available to access'.format(url))\n",
    "            return\n",
    "    \n",
    "        # 將網頁回應的 HTML 傳入 BeautifulSoup 解析器, 方便我們根據標籤 (tag) 資訊去過濾尋找\n",
    "        soup = BeautifulSoup(response.text)\n",
    "    \n",
    "        # 取得文章內容主體\n",
    "        main_content = soup.find(id='main-content')\n",
    "    \n",
    "    # 假如文章有屬性資料 (meta), 我們在從屬性的區塊中爬出作者 (author), 文章標題 (title), 發文日期 (date)\n",
    "        metas = main_content.select('div.article-metaline')\n",
    "        try:\n",
    "            if metas:\n",
    "                if metas[0].select('span.article-meta-value')[0]:\n",
    "                    author = metas[0].select('span.article-meta-value')[0].string\n",
    "                if metas[1].select('span.article-meta-value')[0]:\n",
    "                    title = metas[1].select('span.article-meta-value')[0].string\n",
    "                if metas[2].select('span.article-meta-value')[0]:\n",
    "                    date = metas[2].select('span.article-meta-value')[0].string\n",
    "\n",
    "            # 從 main_content 中移除 meta 資訊（author, title, date 與其他看板資訊）\n",
    "            #\n",
    "            # .extract() 方法可以參考官方文件\n",
    "            #  - https://www.crummy.com/software/BeautifulSoup/bs4/doc/#extract\n",
    "                for m in metas:\n",
    "                    m.extract()\n",
    "                for m in main_content.select('div.article-metaline-right'):\n",
    "                    m.extract()\n",
    "        except:\n",
    "            title = ''\n",
    "            date = ''\n",
    "            author = ''\n",
    "        \n",
    "        # 取得\"留言\"區主體\n",
    "        pushes = main_content.find_all('div', class_='push')\n",
    "        for p in pushes:\n",
    "            p.extract()\n",
    "    \n",
    "        # 假如文章中有包含「※ 發信站: 批踢踢實業坊(ptt.cc), 來自: xxx.xxx.xxx.xxx」的樣式\n",
    "        # 透過 regular expression 取得 IP\n",
    "        # 因為字串中包含特殊符號跟中文, 這邊建議使用 unicode 的型式 u'...'\n",
    "        try:\n",
    "            ip = main_content.find(text=re.compile(u'※ 發信站:'))\n",
    "            ip = re.search('[0-9]*\\.[0-9]*\\.[0-9]*\\.[0-9]*', ip).group()\n",
    "        except Exception as e:\n",
    "            ip = ''\n",
    "    \n",
    "        # 移除文章主體中 '※ 發信站:', '◆ From:', 空行及多餘空白 (※ = u'\\u203b', ◆ = u'\\u25c6')\n",
    "        # 保留英數字, 中文及中文標點, 網址, 部分特殊符號\n",
    "        #\n",
    "        # 透過 .stripped_strings 的方式可以快速移除多餘空白並取出文字, 可參考官方文件 \n",
    "        #  - https://www.crummy.com/software/BeautifulSoup/bs4/doc/#strings-and-stripped-strings\n",
    "        # 過濾\n",
    "        filtered = []\n",
    "        for v in main_content.stripped_strings:\n",
    "        # 假如字串開頭不是特殊符號或不是以 '--' 開頭的, 我們都保留其文字\n",
    "            if v[0] not in [u'※', u'◆'] and v[:2] not in [u'--']:\n",
    "                filtered.append(v)\n",
    "\n",
    "        # 定義一些特殊符號與全形符號的過濾器\n",
    "        expr = re.compile(u'[^一-龥。；，：“”（）、？《》\\s\\w:/-_.?~%()]')\n",
    "        for i in range(len(filtered)):\n",
    "    #         將特殊符號與全形符號替換成''\n",
    "    # re.sub(pattern, replace_str, string, replace_count) replace_count為替換個數\n",
    "            filtered[i] = re.sub(expr, '', filtered[i])\n",
    "    \n",
    "    # 移除空字串, 組合過濾後的文字即為文章本文 (content)\n",
    "        filtered = [i for i in filtered if i] # if i : 將空的內容過濾掉(移除空字串) - 下面有範例\n",
    "        content = ' '.join(filtered) # 將所有內容所組成的 List (也就是 filtered)拼回一個字串，用空白連接\n",
    "    \n",
    "    \n",
    "         # 處理留言區\n",
    "        # p 計算推文數量\n",
    "        # b 計算噓文數量\n",
    "        # n 計算箭頭數量\n",
    "        p, b, n = 0, 0, 0\n",
    "        messages = []\n",
    "        for push in pushes:\n",
    "            try:\n",
    "                # 假如留言段落沒有 push-tag 就跳過\n",
    "                if not push.find('span', 'push-tag'):\n",
    "                    continue\n",
    "        \n",
    "                # 過濾額外空白與換行符號\n",
    "                # push_tag 判斷是推文, 箭頭還是噓文\n",
    "                # push_userid 判斷留言的人是誰\n",
    "                # push_content 判斷留言內容\n",
    "                # push_ipdatetime 判斷留言日期時間\n",
    "                push_tag = push.find('span', 'push-tag').string.strip(' \\t\\n\\r')\n",
    "                push_userid = push.find('span', 'push-userid').string.strip(' \\t\\n\\r')\n",
    "                push_content = push.find('span', 'push-content').strings\n",
    "                push_content = ' '.join(push_content)[1:].strip(' \\t\\n\\r')\n",
    "                push_ipdatetime = push.find('span', 'push-ipdatetime').string.strip(' \\t\\n\\r')\n",
    "            except:\n",
    "                continue\n",
    "            \n",
    "            # 整理打包留言的資訊, 並統計推噓文數量\n",
    "            messages.append({\n",
    "                'push_tag': push_tag,\n",
    "                'push_userid': push_userid,\n",
    "                'push_content': push_content,\n",
    "                'push_ipdatetime': push_ipdatetime})\n",
    "            if push_tag == u'推':\n",
    "                p += 1\n",
    "            elif push_tag == u'噓':\n",
    "                b += 1\n",
    "            else:\n",
    "                n += 1\n",
    "        # 統計推噓文\n",
    "        # count 為推噓文相抵看這篇文章推文還是噓文比較多\n",
    "        # all 為總共留言數量 \n",
    "        message_count = {'all': p+b+n, 'count': p-b, 'push': p, 'boo': b, 'neutral': n}\n",
    "        \n",
    "        # 整理文章資訊\n",
    "        data = PTTArticleItem()\n",
    "        article_id = str(Path(urlparse(response.url).path).stem)\n",
    "        data['url'] = response.url\n",
    "        data['article_id'] = article_id\n",
    "        data['article_author'] = author\n",
    "        data['article_title'] = title\n",
    "        data['article_date'] = date\n",
    "        data['article_content'] = content\n",
    "        data['ip'] = ip\n",
    "        data['message_count'] = message_count\n",
    "        data['messages'] = messages\n",
    "        yield data"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "Python 3",
   "language": "python",
   "name": "python3"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.7.4"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 2
}
