import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask, render_template, request, url_for, redirect

mabitw1url = os.getenv('mabitw1', None)
print(mabitw1url)

if mabitw1url is None:
    print('Specify mabitw1 as environment variable.')
    sys.exit(1)


class search:
    def __init__(self, SearchWord, SearchType):
        self.SearchWord = str(SearchWord)
        self.SearchType = int(SearchType) #4 = 按物品, 1 = 按人物, 2 = 按廣告標語
        self.itemdict = dict()
        self.itemlist = []
        
    def Bebhinn(self, page, SortType, SortOption):       
        try:
            param = {'SearchWord' : self.SearchWord.encode('big5'),
                     'SearchType' : self.SearchType, 
                     'page'       : int(page),
                     'SortType'   : int(SortType), #1 = 玩家, 4 = 物品, 5 = 價格
                     'SortOption' : int(SortOption), #1 = 升序, 2 = 降序
                     'row'        : 7
                    }
            url = mabitw1url

            res = requests.get(url, params = param)
            restext = res.text
            print(res.text)
            bs = BeautifulSoup(restext, "html.parser")

            self.itemdict['NowPage'] = bs.find('advertiseitems')['nowpage']
            self.itemdict['NextPage'] = bool(int(bs.find('advertiseitems')['nextpage']))
            
            msg = bs.findAll('itemdesc')
            timedif = (62198755200-31536000*2-60*60*16)*1000
            for item in msg:
                self.itemdict[item['item_id']] = dict()
                self.itemlist.append(item['item_id'])
                for itemattr in item.attrs.keys():
                    if itemattr == 'start_time':
                        item[itemattr] = datetime.strftime(datetime.fromtimestamp((int(item[itemattr])-timedif)/1000), '%Y-%m-%d %H:%M:%S')
                    if itemattr == 'item_price':
                        pricelist = []
                        w = int(int(item[itemattr])/10000)
                        k = int(int(item[itemattr])%10000)
                        if w  is not 0:
                            pricelist.append(str(w))
                        if k  is not 0:
                            pricelist.append(str(k))
                        else:
                            pricelist.append('')
                        item[itemattr] = '萬'.join(pricelist)
                    self.itemdict[item['item_id']][itemattr] = item[itemattr]
            for item in self.itemlist:
                print('{name} 的價格是 {price}, 販賣人是 {person}, 張貼於 {time}'.format(name=self.itemdict[item]['item_name'],
                                                                        price=self.itemdict[item]['item_price'],
                                                                        person=self.itemdict[item]['char_name'],
                                                                        time=self.itemdict[item]['start_time']))
             

        except :
            print('未發現目標')

app = Flask(__name__)

class turnpage:
    def __init__(self, SearchRequest, url):
        self.SearchRequest = SearchRequest
        
        self.current_page = int(SearchRequest.itemdict['NowPage'])
        self.To_be_Continue = SearchRequest.itemdict['NextPage']
        self.page_one = None
        self.last_page = None
        self.next_page = None
        self.url = url
    def pagelink(self, **attrs):
        if self.current_page == 1:
            attrs['page'] = 1
            self.last_page = self.url_convert(**attrs)
        else:
            attrs['page'] = self.current_page-1
            self.last_page = self.url_convert(**attrs)
        if self.To_be_Continue:
            attrs['page'] = self.current_page+1
            self.next_page = self.url_convert(**attrs)
            attrs['page'] = self.current_page+10
            self.next_ten_page = self.url_convert(**attrs)
        else:
            attrs['page'] = self.current_page
            self.next_page = self.url_convert(**attrs)
            self.next_ten_page = self.url_convert(**attrs)
        attrs['page'] = 1
        self.page_one = self.url_convert(**attrs)
    def url_convert(self, **attrs):
        return(self.url+'?'+'&'.join([key+'='+str(attrs[key]) for key in attrs.keys()])) #替url加上參數


@app.route('/')
def redir():
    return redirect(url_for('main'))

@app.route('/HouseBoard.html', methods=['GET'])
def main():
    SearchRequest = search('', 1)
    
    if request.args.get('page'):
        page = request.args.get('page')
    else:
        page = 1
        
    SearchRequest.Bebhinn(page, 5, 1)

    turnpageHouseBoard = turnpage(SearchRequest, '/HouseBoard.html')
    turnpageHouseBoard.pagelink()
              
    return render_template('HouseBoard.html', itemlist=SearchRequest.itemlist,
                                              itemattr=['char_name', 'item_name', 'item_price', 'comment', 'start_time'],
                                              itemdict=SearchRequest.itemdict,
                           page_one = turnpageHouseBoard.page_one,
                           last_page = turnpageHouseBoard.last_page,
                           next_page = turnpageHouseBoard.next_page,
                           next_ten_page = turnpageHouseBoard.next_ten_page,
                           current_page = turnpageHouseBoard.current_page)


@app.route('/search', methods=['GET'])
def BoardSearch():
    try: 
        if request.args.get('SearchWord'):
            SearchWord = request.args.get('SearchWord')
        else:
            SearchWord = ''
            
        SearchType = request.args.get('SearchType')

        if request.args.get('page'):
            page = request.args.get('page')
        else:
            page = 1

        SearchRequest = search(SearchWord, SearchType)
        SearchRequest.Bebhinn(page, 5, 1)

        turnpageSearch = turnpage(SearchRequest, '/search')
        turnpageSearch.pagelink(SearchWord=SearchWord, SearchType=SearchType)
                    
        return render_template('HouseBoard.html', itemlist=SearchRequest.itemlist,
                                                  itemattr=['char_name', 'item_name', 'item_price', 'comment', 'start_time'],
                                                  itemdict=SearchRequest.itemdict,
                                page_one = turnpageSearch.page_one,
                                last_page = turnpageSearch.last_page,
                                next_page = turnpageSearch.next_page,
                                next_ten_page = turnpageSearch.next_ten_page,
                                current_page = turnpageSearch.current_page)
    except:
        return redirect(url_for('main'))
    
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=os.environ['PORT'])


