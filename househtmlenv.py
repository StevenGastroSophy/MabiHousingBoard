import os
import sys
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from flask import Flask
from flask import render_template
from flask import request

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
            msg = bs.findAll('itemdesc')
            timedif = (62198755200-31536000*2-60*60*16)*1000
            for item in msg:
                self.itemdict[item['item_id']] = dict()
                self.itemlist.append(item['item_id'])
                for itemattr in item.attrs.keys():
                    if itemattr == 'start_time':
                        item[itemattr] = datetime.strftime(datetime.fromtimestamp((int(item[itemattr])-timedif)/1000), '%Y-%m-%d %H:%M:%S')
                    self.itemdict[item['item_id']][itemattr] = item[itemattr]
            for item in self.itemlist:
                print('{name} 的價格是 {price}, 販賣人是 {person}, 張貼於 {time}'.format(name=self.itemdict[item]['item_name'],
                                                                        price=self.itemdict[item]['item_price'],
                                                                        person=self.itemdict[item]['char_name'],
                                                                        time=self.itemdict[item]['start_time']))
             
               
        except PermissionError:
            print('未發現目標')

app = Flask(__name__)
@app.route('/HouseBoard.html', methods=['GET'])
def main():
    SearchRequest = search('', 1)
    if request.args.get('page'):
        page = request.args.get('page')
    else:
        page = 1
    SearchRequest.Bebhinn(page, 5, 1)
    return render_template('HouseBoard.html', itemlist=SearchRequest.itemlist,
                                              itemattr=['char_name', 'item_name', 'item_price', 'comment', 'start_time'],
                                              itemdict=SearchRequest.itemdict)

@app.route('/search', methods=['GET'])
def BoardSearch():
    SearchWord = request.args.get('SearchWord')
    SearchType = request.args.get('SearchType')
    if request.args.get('page'):
        page = request.args.get('page')
    else:
        page = 1
    SearchRequest = search(SearchWord, SearchType)
    SearchRequest.Bebhinn(page, 5, 1)
    return render_template('HouseBoard.html', itemlist=SearchRequest.itemlist,
                                              itemattr=['char_name', 'item_name', 'item_price', 'comment', 'start_time'],
                                              itemdict=SearchRequest.itemdict)
if __name__ == "__main__":
    app.run(host='0.0.0.0',port=os.environ['PORT'])


