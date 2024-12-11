from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import csv
import os
import re
import pandas as pd
import shutil

#プロキシを設定
os.environ["https_proxy"] = "http://wwwproxy.kanazawa-it.ac.jp:8080"

#気象庁のWEBサイトにアクセスして、HTMLを取得する関数
def Data_getter(area_code):
    chrome_options = Options()
    chrome_options.add_argument("--headless")#ヘッドレスモード(画面にブラウザを表示しない)

    #プロキシの設定
    proxy = "http://wwwproxy.kanazawa-it.ac.jp:8080" #プロキシ
    chrome_options.add_argument(f'--proxy-server={proxy}')#プロキシを設定

    #ChromeDriverのインスタンスを作成
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service = service, options = chrome_options)

    #urlを指定 area_codeは関数の引数で受け取る
    #市まで
    #url = f"https://www.jma.go.jp/bosai/#pattern=default&area_type=class20s&area_code={area_code}"
    #県まで
    url = f"https://www.jma.go.jp/bosai/#pattern=default&area_type=offices&area_code={area_code}"

    #ページを取得
    driver.get(url)
    time.sleep(10)

    #読み込んだページからHTMLを取得
    html = driver.page_source

    #デバッグ用にhtmlをテキストファイルに書き出し
    Data_writer("HTML_data", html)

    return html

#HTMLを解析する
def HTML_analyzer(row_html, RESULT):
    print("Analysing html")
    #BeautifulSoupオブジェクトを作成
    soup = BeautifulSoup(row_html, "html.parser")#html.parserはpython標準のHTML解析器

    #classとidを用いて欲しい部分を切り取り
    important_info = soup.find("div", class_ = "bosaitop-col", id = "bosaitop-col0")#bosaitop-col0はwebサイトの右半分を表す
    #このときimportant_infoはbs4.element.Tag型のデータ

    #デバッグ用に書き出し
    Data_writer("important_part", str(important_info))

    #ここから情報別にデータを取り出す。

    #発表中の防災情報
    announce_disaster = soup.find("div", class_ = "bosaitop-container bosaitop-infocontainer", id = "bosaitop-panel_window", attrs={"value": "panel"})
    Data_writer("announce_disaster", str(announce_disaster))
    Data_extractor_disaster(announce_disaster, RESULT) #解析関数の呼び出し

    #天気予報
    Weather_Forecast = soup.find("div", class_ = "contents-wide-table")
    Data_writer("Weather_Forecast", str(Weather_Forecast))
    Data_extractor_weather(Weather_Forecast, RESULT)

    #地震情報
    earthquake_info = soup.find("div", class_ = "bosaitop-container bosaitop-infocontainer", id = "bosaitop-earthquake_window", attrs={"value": "earthquake"})
    Data_writer("earthquake_info", str(earthquake_info))

    print("Finish analysing")

def Data_extractor_disaster(announce_disaster,RESULT):
    print("Extract disaster data from the html")
    element = announce_disaster.find_all("div", class_ = "panel panel-forecast-level20")
    with open(f"./{RESULT}/main_data.txt", "a", encoding = "utf-8") as file:
        file.write("発令中の警報情報\n")
        for i in element:
            file.write(str(i.get("title"))+ "\n")
            file.write(str(i.get_text()) + "\n")
    print("finish extracting disaster data")

def Data_extractor_weather(Weather_Forecast, RESULT):
    #データ用のリストを作成
    Date_list = []
    temp_list = []
    #Weather_list = []
    #chance_of_rain = []
    #Reliability = []
    #LH_temperature = []

    print("Extract weather data from the html")
    temp1 = Weather_Forecast.find("div", class_ = "contents-wide-table-fix")
    temp2 = temp1.find("table", class_ = "forecast-table")
    tr_data_th= temp2.find("tr", class_ = "contents-header contents-bold-top")
    #ヘッダー部分の抽出
    element_th = tr_data_th.find_all("th")
    for i in element_th:
        print(f"{i.get_text()} was printed")
        Date_list.append(i)
    #ヘッダー(日付)以外の部分の抽出
    tr_data_none = temp2.find_all('tr', class_=lambda x: x is None)
    for i in tr_data_none:
        element_td = i.find_all("td")
        for j in element_td:
            print(f"{j.get_text()} was printed")
            #一時的にtempリストに保存。後で8つ跳びに取り出す。
            temp_list.append(j.get_text())

    temp_list_length = len(temp_list)
    print(f"Temp list length : {temp_list_length}")

    with open(f"./{RESULT}/main_data.txt", "a", encoding = "utf-8") as file:
        file.write("日付 : 天気 : 降水確率 : 信頼度 : 最低気温/最高気温\n")
        for i in range(0,8):
            file.write(f"{Date_list[i].get_text()} : ")
            for j in range(i,temp_list_length,8):
                file.write(f"{temp_list[j]} : ")

            file.write("\n")


def Data_extractor_earthquake():
    print("Extract earthquake data from the html")

#テキストファイルにデータを書き出す関数
def Data_writer(name, data):
    #デバッグファイル保存用のディレクトリを作成、既にある場合は何もしない
    Directory_name = "debug"
    if not os.path.exists(Directory_name):
        os.mkdir(Directory_name)

    #書き込み、既にある場合上書き
    with open(f"./{Directory_name}/{name}.txt", "w", encoding = "utf-8") as file:
        file.write(data)
        print(f"Data was written in {name}.txt")


#結果ファイルを初期化する関数
def file_reset(Directory_name):
    if os.path.exists(Directory_name):
        shutil.rmtree(f"./{Directory_name}")
    os.mkdir(Directory_name)
    with open(f"./{Directory_name}/main_data.txt", "a", encoding = "utf-8") as file:
        file.write("抽出結果\n")
    print("結果ファイルの初期完了")

#結果を結果ファイルのディレクトリを指定
RESULT = "RESULT"
#結果ファイルの初期化
file_reset("RESULT")

#HTMLデータを取得(1721200は野々市市のエリアコード)
#row_html = Data_getter(170000)

#テスト用に固定のHTMLを用いる
with open("./debug/HTML_data.txt", "r", encoding = "utf-8") as file:
    HTML_analyzer(file,RESULT)