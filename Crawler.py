import time
import requests
import json

import os

from selenium import webdriver
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from bs4 import BeautifulSoup, element

from selenium.webdriver.common.keys import Keys

import datetime

from selenium.webdriver.chrome.service import Service
from subprocess import CREATE_NO_WINDOW


#Crawler クラス
class Crawler:

    # コンストラクタ（設定）
    def __init__(self):
        # webdriver & browser(Headless Mode)　設定と準備
        self.chrome_options = webdriver.ChromeOptions()
        self.chrome_options.add_argument("--headless")
        self.chrome_options.add_argument("--ignore-certificate-errors")
        self.chrome_options.add_argument("--incognito")
        self.chrome_options.add_argument("--auto-open-devtools-for-tabs")
        self.chrome_options.add_argument("--disable-extensions")

        # chrome の log を見るための設定
        self.d = DesiredCapabilities.CHROME
        self.d['goog:loggingPrefs'] = {'performance': 'ALL'}

        new_service = Service(os.path.dirname(__file__) + '\\chromedriver.exe')
        new_service.creationflags = CREATE_NO_WINDOW
        # webdriver & browser 起動
        self.driver = webdriver.Chrome(executable_path=os.path.dirname(__file__) + '\\chromedriver.exe',options=self.chrome_options,desired_capabilities=self.d,service=new_service)

        # 整形したurl_collectorリスト
        self.url_collector = []

        # 入力できる物件のリストを準備
        self.input_id_list = []
        self.submit_button_id_list = []
        self.form_id_list = []

        # htmlソースコードの中のelementを保存するリスト
        self.elements = []

        # 整形したHTMLソースコード
        self.html = ""

        # クローラーのスタートURLが間違えていた場合のメッセージ
        self.url_error = ""

    # start(ドメイン)
    def start(self,start_domain):

        current_url = start_domain


        # 整形したurl_collectorリスト
        self.url_collector.append(current_url)

        # 整形したurlをテスト、失敗の場合はプログラムを停止
        r = requests.get(current_url)
        if r.status_code != requests.codes.ok:
            #print("URL incorrect!")
            self.url_error = "URL incorrect!"
            #exit()

        # webdriver(Chrome)でURLを開く
        self.driver.get(start_domain)
        current_url = self.driver.current_url
        time.sleep(5)

        # htmlソースコードを整形
        self.html = self.driver.page_source
        time.sleep(5)
        parsed_html = BeautifulSoup(self.html, "html.parser")
        parsed_html = parsed_html.prettify()
        self.html = parsed_html

        # ソースコードの中の"href"属性を取り出す
        # 所得したURLをテスト
        # 200(success)が出たら,url_collectorリストに保存
        for item in str(self.html).split(" "):
            if "href=" in item:
                item = item.split("\"",2)[1]
                try:
                    r = requests.get(item)
                except:
                    pass
                else:
                    if r.status_code == requests.codes.ok:
                        self.url_collector.append(item)
                        continue
        # 失敗の場合, URLを整形して試す
        # max_try整形して試す回数: 1
                max_try = 1
                current_try = 0
                while current_try < max_try:
                    current_try += 1
        # 整形が必要なURL:
        # 0. //url
        # 1. /sub-url
        # 2. ./sub-url
        # 3. ../sub-url
        # 4. #/sub-url
        # 5. sub-url
        # 以上のURLを　http://url/　のパターンに整形してみる
        # Fix 0~4.
                    # Fix 0.
                    if item.startswith("//"):
                        item = "http:" + item
                    # Fix 1.
                    elif item.startswith("/"):
                        item = current_url + item.split("/",1)[1]
                    # Fix 2.
                    elif item.startswith("./"):
                        item = current_url + item.split("./",1)[1]
                    # Fix 3.
                    elif item.startswith("../"):
                        item = current_url.rsplit("/",2)[0] + item.split("../",1)[1]
                    # Fix 4.
                    elif item.startswith("#/"):
                        item = current_url + item
        # 整形したURLをテスト( if r.status_code == requests.codes.ok)
        # Fix 5.はexceptの中にやる
                    try:
                        r = requests.get(item)
                    except:
                        # Fix 5.
                        r = requests.get(current_url + item)
                        if r.status_code == requests.codes.ok:
                            item = current_url + item
                            self.url_collector.append(item)
                            break
                    else:
                        if r.status_code == requests.codes.ok:
                            self.url_collector.append(item)
                            break

        # REST APIを使っているウエイブアプリに対するURL修正
        for i in range(len(self.url_collector)):
            if '#/#/' in str(self.url_collector[i]):
                self.url_collector[i] = str(self.url_collector[i]).replace('#/#/', '#/', 1)

        # htmlソースコードの中の "input" tag　を input_id_list に保存
        for item in str(self.html).split(">"):
            if "<input " in item:
                item = item.strip()
                item = item.split(">")[0]
                if "id=" in item:
                    item = item.split(" id=\"")[1]
                    item = item.split("\"")[0]
                    self.input_id_list.append(item)

        # seleniumの自動化機能を使って自動入力 & enterを押す
        try:
            self.driver.find_element_by_id(self.input_id_list[0]).send_keys("\'")
            self.driver.find_element_by_id(self.input_id_list[0]).send_keys(Keys.ENTER)
            if self.driver.current_url != current_url:
                self.driver.get(current_url)
        except:
            pass

        for item1 in range(len(self.input_id_list)):
            element = self.driver.find_element_by_id(self.input_id_list[item1])
            try:
                element.send_keys("\'")
            except:
                pass
            for item2 in range(len(self.input_id_list)):
                if item2 != item1:
                    element = self.driver.find_element_by_id(self.input_id_list[item2])
                    try:
                        element.send_keys("\'")
                        element.send_keys(Keys.ENTER)
                    except:
                        pass
                    if self.driver.current_url != current_url:
                        self.driver.get(current_url)

        # chrome から log を取得し、その中のurlを保存
        for entry_json in self.driver.get_log('performance'):
            entry = json.loads(entry_json['message'])
            if entry['message']['method'] != 'Network.requestWillBeSent' :
                continue
            self.url_collector.append(entry['message']['params']['request']['url'])

        self.url_collector = list(dict.fromkeys(self.url_collector))

    # クロールしたURLをprint (debug用)
    def print_url(self):
        for url in self.url_collector:
            print(url,end="\n")

    # Chrome driverを終了
    def quit(self):
        self.driver.quit()





# SQL(crawler) , crawlerはあらかじめ宣言したCrawlerインスタンスを代入
# 例 : sql = SQL(crawler)
class SQL:
    def __init__(self,crawler):

        # cralwerインスタンス代入
        self.crawler = crawler

        #対象URL
        self.scan_url = ""

        # seleniumが自動入力できる element のリストを準備
        self.input_id_list = []
        self.submit_button_id_list = []
        self.form_id_list = []

        # htmlソースコードの中のelementを保存するリスト
        self.elements = []

        # 脆弱性がある url や レスポンスを収集する辞書を準備
        self.v_url = {}

        # レポートのためのリスト
        self.report_url = []
        self.report_param = []
        self.report_dangerous = []
        self.report_detail = []
        self.report_source = []
        self.report_response = {}
        self.report_response_data = {}
            
    # SQL Injection
    def scan(self,url):

        # driverを目標urlに移動する
        self.crawler.driver.get(url)
        current_url = self.crawler.driver.current_url
        self.scan_url = current_url

        # log をクリアする
        self.crawler.driver.get_log('performance')

        time.sleep(5)
        
        # htmlソースコードの中の "input" tag　を input_id_list に保存
        for item in str(self.crawler.html).split(">"):
            if "<input " in item:
                item = item.strip()
                item = item.split(">")[0]
                if "id=" in item:
                    item = item.split(" id=\"")[1]
                    item = item.split("\"")[0]
                    self.input_id_list.append(item)

        # 各 id の element に key を入力する
        try:
            self.crawler.driver.find_element_by_id(self.input_id_list[0]).send_keys("\'")
            self.crawler.driver.find_element_by_id(self.input_id_list[0]).send_keys(Keys.ENTER)
            if self.crawler.driver.current_url != current_url:
                self.crawler.driver.get(current_url)
        except:
            pass
        
        # 自動操作で入力、送信
        for item1 in range(len(self.input_id_list)):
            element = self.crawler.driver.find_element_by_id(self.input_id_list[item1])
            try:
                element.send_keys("\'")
            except:
                pass
            for item2 in range(len(self.input_id_list)):
                if item2 != item1:
                    element = self.crawler.driver.find_element_by_id(self.input_id_list[item2])
                    try:
                        element.send_keys("\'")
                        element.send_keys(Keys.ENTER)
                    except:
                        pass
                    if self.crawler.driver.current_url != current_url:
                        self.crawler.driver.get(current_url)
        
        # GOOGLE CHROMEから取得したエラーメッセージを分析する
        logs_raw = self.crawler.driver.get_log("performance")
        logs = [json.loads(lr["message"])["message"] for lr in logs_raw]
        for log in logs:
            if log["method"] == "Network.responseReceived" and "json" in log["params"]["response"]["mimeType"]:
                request_id = log["params"]["requestId"]
                resp_url = log["params"]["response"]["url"]
                if "error" and "sql" and "\"SELECT *" in str(self.crawler.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id})):
                    if resp_url not in self.v_url.keys():
                        self.report_response = log["params"]["response"]
                        self.report_response_data = self.crawler.driver.execute_cdp_cmd("Network.getRequestPostData", {"requestId": request_id})
                        raw_log = str(self.crawler.driver.execute_cdp_cmd("Network.getResponseBody", {"requestId": request_id}))
                        self.v_url[resp_url] = raw_log
                        # 文字化け修正、レポート関連
                        self.string_report_fix(resp_url)
        if len(self.report_url) == 0:
            # 脆弱性がない場合
            self.report_url.append(self.scan_url)
            self.report_source.append("")
            self.report_detail.append("脆弱性が発見されませんでした。")
            self.report_dangerous.append("")
            self.report_param.append("")

                  
    # 文字化け修正、レポート関連
    def string_report_fix(self,resp_url):
        if resp_url in self.v_url.keys():
            fix_1 = str(self.v_url[resp_url]).replace('\\\\','\\')
            fix_2 = fix_1.replace('\\\\','\\')
            fix_3 = fix_2.replace('\\n ','\n')
            fix_4 = fix_3.replace('\\'+'\'','\'')
            fix_5 = fix_4.replace('\\'+'n'+'}','\n'+'}')
            fix_6 = fix_5.replace("\\"+"\"","\"")
            if "SELECT * FROM" in fix_6:
                # report_urlに記入
                self.report_url.append(resp_url)
                # report_sourceに記入
                self.report_source.append(fix_6)
                # 他のレポート項目に記入
                self.report_detail.append("脆弱性があるSQLシーケンスを発見しました。")
                self.report_dangerous.append("高")
                self.report_param.append("")


    # レポート出力
    def report_output(self):
        # 目標：./レポート/SQLインジェクション/SQL_{時間}.txt を出力
        # 時間 string 作成
        dt = datetime.datetime.now()
        dt_string = str(dt.year) + "-" + str(dt.month) + "-" + str(dt.day) + "_" 
        if int(dt.hour) < 10 :
            dt_string = dt_string + "0" + str(dt.hour) + "-"
        else :
            dt_string = dt_string + str(dt.hour) + "-"
        if int(dt.minute) < 10 :
            dt_string = dt_string + "0" + str(dt.minute) + "-"
        else :
            dt_string = dt_string + str(dt.minute) + "-"
        if int(dt.second) < 10 :
            dt_string = dt_string + "0" + str(dt.second)
        else :
            dt_string = dt_string + str(dt.second)


        with open('./レポート/SQLインジェクション/' + 'SQL_' + dt_string + '.txt', mode='w', encoding='utf-8') as f:
            f.write('URL: ' + self.report_url[0] + '\n')
            f.write('パラメータ: ' + self.report_param[0] + '\n')
            f.write('脆弱性名: ' + 'SQLインジェクション' + '\n')
            f.write('詳細: ' + self.report_detail[0] + '\n')
            f.write('危険度: ' + self.report_dangerous[0] + '\n')
            if self.report_dangerous[0] != "":
                f.write('\n')
                f.write('リクエスト:' + '\n')
                f.write('\t' + "メソッド: " + "POST" + '\n')
                f.write('\t' + "mimeType: " + self.report_response['mimeType'] + '\n')
                f.write('\t' + "protocol: " + self.report_response['protocol'] + '\n')
                f.write('\t' + "remoteIPAddress: " + self.report_response['remoteIPAddress'] + '\n')
                f.write('\t' + "remotePort: " + str(self.report_response['remotePort']) + '\n')
                f.write('\t' + "status code: " + str(self.report_response['status']) + '\n')
                f.write('\t' + "status text: " + self.report_response['statusText'] + '\n')
                f.write('\n')
                f.write('リクエストヘッダー:' + '\n')
                f.write('\t' + 'Access-Control-Allow-Origin: ' + self.report_response['headers']['Access-Control-Allow-Origin'] + '\n')
                f.write('\t' + 'Connection: ' + self.report_response['headers']['Connection'] + '\n')
                f.write('\t' + 'Content-Encoding: ' + self.report_response['headers']['Content-Encoding'] + '\n')
                f.write('\t' + 'Content-Type: ' + self.report_response['headers']['Content-Type'] + '\n')
                f.write('\t' + 'X-Content-Type-Options: ' + self.report_response['headers']['X-Content-Type-Options'] + '\n')
                f.write('\t' + 'X-Frame-Options: ' + self.report_response['headers']['X-Frame-Options'] + '\n')
                f.write('\n')
                f.write('リクエストペイロード: ' + self.report_response_data['postData'] + '\n')
                f.write('\n')
                f.write('リスポーン:' + '\n')
                f.write(self.report_source[0])
