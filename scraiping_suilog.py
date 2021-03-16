import requests
from bs4 import BeautifulSoup
import re
import pandas as pd
import time
import tqdm

import mysql.connector as mysql
from mysql.connector import errorcode

class Tabelog:
    """
    食べログスクレイピングクラス
    test_mode=Trueで動作させると、最初のページの３店舗のデータのみを取得できる
    """
    def __init__(self, base_url, test_mode=False, p_ward='東京', begin_page=2, end_page=3):

        # 変数宣言
        self.store_id = ''
        self.store_id_num = 0
        self.store_name = ''
        self.near_st = ''
        self.store_type = ''
        self.score = 0
        self.smoking = ''
        self.address = ''
        self.lat = ''
        self.lng = ''
        self.ward = p_ward
        self.url = item_url = ''
        self.columns = ['store_id', 'store_name', 'store_type', 'score', 'smoking', 'address','ward', 'station', 'url']
        self.df = pd.DataFrame(columns=self.columns) #最終的にインスタンスから呼び出すメソッド
        self.__regexcomp = re.compile(r'\n|\s') # \nは改行、\sは空白

        page_num = begin_page # 店舗一覧ページ番号

        if test_mode: #test_modeがFalse(全てのページに対して実行)の時
            #base_urlに数字を足すとページの番号が進む
            list_url = base_url + str(page_num) +  '/?Srt=D&SrtT=rt&sort_mode=1&select_sort_flg=1' #食べログの点数ランキングでソートする際に必要な処理
            self.scrape_list(list_url, mode=test_mode) #scrap_listメソッドの呼び出し

        else: #test_modeがTrue(取得するページの枚数を制限)の時
            while True: #breakが出るまでエンドレスに繰り返し
                #base_urlに数字を足すとページの番号が進む
                list_url = base_url + str(page_num) +  '/?Srt=D&SrtT=rt&sort_mode=1&select_sort_flg=1' #食べログの点数ランキングでソートする際に必要な処理
                #scrap_listメソッドを呼び出してFalseの時->break
                if self.scrape_list(list_url, mode=test_mode) != True:
                    print('1')
                    break

                # INパラメータまでのページ数データを取得する
                # 現在のページが指定した枚数以上の時->break
                if page_num >= end_page:
                    print('2')
                    break

                #ページを1つ進める
                page_num += 1
        return

    def scrape_list(self, list_url, mode):
        """
        店舗一覧ページのパーシング
        """
        r = requests.get(list_url)
        #urlが一致しない時->False
        if r.status_code != requests.codes.ok:
            print('3')
            return False

        #BeautifulSoupクラスのオブジェクトを生成
        soup = BeautifulSoup(r.content, 'html.parser')
        #店名一覧を取得して、配列として変数に代入
        soup_a_list = soup.find_all('a', class_='list-rst__rst-name-target')

        #len関数で要素数を確認、0以下ならばFalse
        if len(soup_a_list) == 0:
            print('4')
            return False

        if mode: #test_modeがFalse(全てのページに対して実行)の時
            for soup_a in soup_a_list[:2]:
                item_url = soup_a.get('href') # 店の個別ページURLを取得
                self.url = item_url
                self.store_id_num += 1 #プロパティをインクリメント
                self.scrape_item(item_url, mode) #メソッドの呼び出し

        else: #test_modeがTrue(取得するページの枚数を制限)の時
            for soup_a in soup_a_list:
                item_url = soup_a.get('href') # 店の個別ページURLを取得
                self.url = item_url
                self.store_id_num += 1
                self.scrape_item(item_url, mode)

        return True

    def scrape_item(self, item_url, mode):
        """
        個別店舗情報ページのパーシング
        """
        start = time.time()

        r = requests.get(item_url)
        if r.status_code != requests.codes.ok:
            print(f'error:not found{ item_url }')
            print('5')
            return

        soup = BeautifulSoup(r.content, 'html.parser')

        # 店舗名称取得
        # <h2 class="display-name">
        #     <span>
        #         麺匠　竹虎 新宿店
        #     </span>
        # </h2>
        store_name_tag = soup.find('h2', class_='display-name')      
        store_name = store_name_tag.span.string
        print('{}→店名：{}'.format(self.store_id_num, store_name.strip()), end='')
        self.store_name = store_name.strip()

        # 評価点数取得
        #<b class="c-rating__val rdheader-rating__score-val" rel="v:rating">
        #    <span class="rdheader-rating__score-val-dtl">3.58</span>
        #</b>
        rating_score_tag = soup.find('b', class_='c-rating__val')
        rating_score = rating_score_tag.span.string
        #print('  評価点数：{}点'.format(rating_score), end='')
        self.score = rating_score

        # ジャンル取得
        store_type = soup.find_all('span', class_="linktree__parent-target-text")
        if not store_type:
            print('5.5')
            return
        #print(store_type[0].contents[0]) # 最寄り駅
        #print(store_type[-1].contents[0]) # ジャンル
        self.store_type = store_type[-1].contents[0]
        self.near_st = store_type[0].contents[0]


        # 喫煙情報取得
        no_smoke = '禁煙'
        no_smoke_only_lunch = 'ランチタイム'
        elem1 = soup.find('p', class_="p-input-form__line")
        elem2 = soup.find('p', class_="rstinfo-table__notice")

        if not elem1:
            print('不明なので処理対象外')
            return

        if no_smoke in elem1.text:
            print('禁煙なので処理対象外')
            return
        
        if no_smoke not in elem1.text:
            print(elem1.text)
            self.smoking = elem1.text

        """
        if no_smoke in elem2:
            if 'ランチタイム' in elem2:
                print(elem2.text)
                self.smoking = elem2.text

            print('禁煙なので処理対象外')
            return
        """

        if self.smoking == '':
            print('値が入っていないので処理対象外')
            return


        # 住所情報取得
        address = soup.find('p', class_='rstinfo-table__address')
        if not address:
            print('住所情報がないので処理対象外')
            return
        self.address = address.text


        # 住所を緯度経度へ変換
        """
        addressに住所を指定すると緯度経度を返す。

        >>> coordinate('東京都文京区本郷7-3-1')
        ['35.712056', '139.762775']
        """
        URL = 'http://www.geocoding.jp/api/'
        payload = {'q': self.address}
        html = requests.get(URL, params=payload)
        soup = BeautifulSoup(html.content, "html.parser")
        if soup.find('error'):
            raise ValueError(f"Invalid address submitted. {address}")
        self.lat = soup.find('lat').text
        self.lng = soup.find('lng').text

        # データベースに挿入
        self.insert_db()
        print('10')
        return

        """
        # データフレームの生成
        self.make_df()
        print('7')
        return
        """
    """
    # データフレーム使用のメソッド
    def make_df(self):
        self.store_id = str(self.store_id_num).zfill(8) #0パディング
        se = pd.Series([self.store_id, self.store_name, self.score, self.smoking, self.address, self.ward, self.url], self.columns) # 行を作成
        self.df = self.df.append(se, self.columns) # データフレームに行を追加
        print('8')
        return
    """
    
    def insert_db(self):
        # dbへ挿入するデータ(店情報)を配列に入れる
        each_store = [(str(self.store_name), str(self.store_type), str(self.score), str(self.smoking), str(self.address), str(self.ward), str(self.near_st))]
        print(each_store)
        # dbへ挿入するデータ(url)を配列に入れる
        each_url = [(str(self.url))]
        print(each_url)
        # dbへ挿入するデータ(geo)を配列に入れる
        each_geo = [(str(self.lat), str(self.lng))]
        print(each_geo)


        db=mysql.connect(
            host="db",
            user="admin",
            passwd="suilogpass",
            port=3306,
            database="suilog_db"
        )
        cursor=db.cursor()
 
        # データベースを選択
        cursor.execute("USE suilog_db")
        db.commit()
 
        # データを挿入
        # restaurant詳細情報の挿入
        insert_smoke_restaurants = "INSERT INTO stores (name, type, score, smoking, address, ward, station) VALUES (%s,%s,%s,%s,%s,%s,%s);"

        for each_store_data in each_store:
            cursor.execute(insert_smoke_restaurants, each_store_data)


        # urlの挿入
        insert_restaurant_urls = "INSERT INTO urls (url) VALUES (%s);"
        cursor.execute(insert_restaurant_urls, each_url)


        # 緯度経度の挿入
        insert_restaurant_geos = "INSERT INTO geos (lat, lng) VALUES (%s,%s);"
        for each_geo_data in each_geo:
            cursor.execute(insert_restaurant_geos, each_geo_data)

        db.commit()
        return


tokyo_restaurant_smoking = Tabelog(base_url="https://tabelog.com/tokyo/rstLst/",test_mode=False, p_ward='東京')

#CSV保存
#tokyo_restaurant_smoking.df.to_csv("tokyo_ramen_review.csv")

