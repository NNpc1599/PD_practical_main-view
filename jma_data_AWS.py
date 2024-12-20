from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
from bs4 import BeautifulSoup
import json


#気象庁のWEBサイトにアクセスして、HTMLを取得する関数
def Data_getter(area_code):
    chrome_options = Options()
    chrome_options.add_argument("--headless")#ヘッドレスモード(画面にブラウザを表示しない)

    #ChromeDriverのインスタンスを作成
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service = service, options = chrome_options)
    print("Chrome Driver instance was created")

    #urlを指定 area_codeは関数の引数で受け取る
    #area_codeの長さからURLを場合分けする
    area_code_length = len(str(abs(area_code)))
    #市
    if(area_code_length == 7):
        url = f"https://www.jma.go.jp/bosai/#pattern=default&area_type=class20s&area_code={area_code}"
    #県
    elif(area_code_length == 6):
        url = f"https://www.jma.go.jp/bosai/#pattern=default&area_type=offices&area_code={area_code}"
    else:
        return None

    #ページを取得
    driver.get(url)
    time.sleep(10)
    print("Get HTML data from web")

    #読み込んだページからHTMLを取得
    html = driver.page_source
    print("HTML : complete")

    return html

#HTMLを解析する
def HTML_analyzer(row_html):
    print("Analysing html")
    #BeautifulSoupオブジェクトを作成
    soup = BeautifulSoup(row_html, "html.parser")#html.parserはpython標準のHTML解析器

    #classとidを用いて欲しい部分を切り取り
    important_info = soup.find("div", class_ = "bosaitop-col", id = "bosaitop-col0")#bosaitop-col0はwebサイトの右半分を表す
    #このときimportant_infoはbs4.element.Tag型のデータ

    #ここから情報別にデータを取り出す。

    #地区名の取得と辞書に記録
    area = soup.find("head").find("title").text
    area_title = f"地区名:{area}"
    result["Area_name"] = area_title

    #発表中の防災情報
    announce_disaster = soup.find("div", class_ = "bosaitop-container bosaitop-infocontainer", id = "bosaitop-panel_window", attrs={"value": "panel"})
    Data_extractor_disaster(announce_disaster) #解析関数の呼び出し

    #天気予報
    Weather_Forecast = soup.find("div", class_ = "contents-wide-table")
    Data_extractor_weather(Weather_Forecast)

    #地震情報
    earthquake_info = soup.find("div", class_ = "bosaitop-container bosaitop-infocontainer", id = "bosaitop-earthquake_window", attrs={"value": "earthquake"})
    Data_extractor_earthquake(earthquake_info)

    print("Finish analysing : all data was written in main_data.txt")

def Data_extractor_disaster(announce_disaster):
    temp = []
    print("Extract disaster data from the html")
    element = announce_disaster.find_all("div", class_ = "bosaitop-contentscontainer panel_container", id = "bosaitop-bosai_panel_div")
    for i in element:
        sub_element = i.find("div", class_="panel")
        if sub_element:
            temp.append(f"{str(sub_element.get('title'))} : {str(sub_element.get_text())}")
    result["Alert"] = temp
    print("finish extracting disaster data")

def Data_extractor_weather(Weather_Forecast):
    #データ用のリストを作成
    Date_list = []
    temp_list = []
    Weather_list = []
    chance_of_rain = []
    Reliability = []
    LH_temperature = []

    print("Extract weather data from the html")
    temp1 = Weather_Forecast.find("div", class_ = "contents-wide-table-fix")
    temp2 = temp1.find("table", class_ = "forecast-table")
    tr_data_th= temp2.find("tr", class_ = "contents-header contents-bold-top")
    #ヘッダー部分の抽出
    element_th = tr_data_th.find_all("th")
    for i in element_th:
        #print(f"{i.get_text()} was printed")
        Date_list.append(i)
    #ヘッダー(日付)以外の部分の抽出
    tr_data_none = temp2.find_all('tr', class_=lambda x: x is None)
    for i in tr_data_none:
        element_td = i.find_all("td")
        for j in element_td:
            print(f"{j.get_text()} was printed")
            temp_list.append(j.get_text())

    temp_list_length = len(temp_list)
    print(f"Temp list length : {temp_list_length}")


    for i in range(0,temp_list_length):
        print(f"temp_list_check : {temp_list[i]}")
        if i < 7:
            Weather_list.append(temp_list[i])
        elif i < 14:
            chance_of_rain.append(temp_list[i])
        elif i < 21:
            Reliability.append(temp_list[i])
        elif i < 28:
            LH_temperature.append(temp_list[i])

        #print(f"list append with num {i} : {temp_list[i]}")

    print("category list : completed")

    temp = []
    for i in range(0,7):
        print(i)
        print(LH_temperature)
        temp.append(f"日付:{Date_list[i + 1].get_text()},天気:{Weather_list[i]},降水確率:{chance_of_rain[i]}%,信頼性:{Reliability[i]},最低/最高気温:{LH_temperature[i]}")
    result["Weather"] = temp

    print("finish extracting weather data")

def Data_extractor_earthquake(earthquake_info):
    print("Extract earthquake data from the html")
    temp = earthquake_info.find("table")
    result_temp = []
    if temp:
        content_title= temp.find("tr", class_ = "contents-title")
        title_element = content_title.find_all("th")

        main_info = temp.find_all("tr", class_ = "contents-clickable contents-clickable-highlight")

        for i in title_element:
            result_temp.append(f"{i.get_text()} : ")

        for i in main_info:
            result_temp.append(f"{i.get_text()}")
    else:
            result_temp.append("最近30日に発表された地震情報はありません。")

    result["earthquake"] = result_temp
    print("finish extracting earthquake data")

keys = ["Area_name", "Alert", "Weather", "earthquake"]
result = dict.fromkeys(keys)
#HTMLデータを取得(1721200は野々市市のエリアコード、170000は石川県のエリアコード)
row_html = Data_getter(1721200)
HTML_analyzer(row_html)
print(result)
print("----")
print(json.dumps(result, ensure_ascii = False, indent = 4))