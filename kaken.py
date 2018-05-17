from selenium import webdriver

from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.options import Options
import time # sleep処理に必要
import pymysql # SQL
import datetime # フォーマット
import sys
from urllib.parse import urlparse, parse_qs
import re
import unicodedata
from email.mime.text import MIMEText
from email.header import Header
import smtplib
from datetime import datetime
from random import shuffle
import concurrent.futures
from  concurrent.futures import ProcessPoolExecutor
import multiprocessing
from pytz import timezone
from dateutil import parser
from urllib.parse import urlsplit


def create_chrome():
    options = Options()
    # options.binary_location = '/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary'
    # options.add_argument('--headless')

    return webdriver.Chrome(executable_path='chromedriver', chrome_options=options)
    

def start_crawle():

    # browser = webdriver.Chrome(executable_path='chromedriver')
    browser = create_chrome()
    
    browser.get("https://kaken.nii.ac.jp/ja/search/?qf=沖縄")

    browser.find_elements_by_class_name("btn-toggle-advsearch-label")[0].click()

    time.sleep(1)

    browser.find_elements_by_name("qf")[0].send_keys("沖縄")
    browser.find_elements_by_class_name("searchbtn")[0].click()
    
    time.sleep(10)
    

if len(sys.argv) > 1:
    if sys.argv[1] == "k":
        print("** run kaken mode")


        exit()
    elif sys.argv[1] == "d":
        exit()
else:
    
    class Article:

        def __init__(self):
            self.id = None
            self.title = None
            self.fields = []
            self.institutions = []
            self.keywords = []
            self.names = []
            self.searchStartFiscalYear = None
            self.searchEndFiscalYear = None

            self.directCost = None
            self.indirectCost = 0
            self.totalCost = None

        def __repr__(self):
            return f"Article {self.id} {self.keywords}"

        def __hash__(self):
            return hash(self.id)

        def __eq__(self, other):
            return self.id == other.id

        def keywords_text(self):
            return  "，".join(self.keywords)

        def names_text(self):
            return "，".join(self.to_name(self.names))

        def fields_text(self):
            return "，".join(self.fields)

        def to_name(self, names):
            l = []
            for n in names:
                if n[0] != "":
                    l.append(f"{n[1]} ({n[0]})")
                else:
                    l.append(f"{n[1]}")

            return l

    def load(file):

        import xml.etree.ElementTree as ET

        articles = []

        tree = ET.parse(file)
        root = tree.getroot()
        print(root)
        for el in root:
            print(el)
            a = Article()
            articles.append(a)

            # for node in el.getiterator("identifier"):
            #     print(node.tag, node.attrib, node.text)
            a.id = el.attrib["id"]

            print(a.id)
            summ = list(el.getiterator("summary"))[0]

            for node in summ.getiterator("title"):
                print(node.tag, node.attrib, node.text)
                a.title = node.text.replace(",","，")


            for node in summ.getiterator("category"):
                print(node.tag, node.attrib, node.text)
            for node in summ.getiterator("field"):
                print(node.tag, node.attrib, node.text)
                a.fields.append(node.text.replace(",","，"))
                
            for node in summ.getiterator("institution"):
                print(node.tag, node.attrib, node.text)
                a.institutions.append(node.text.replace(",","，"))

            for node in summ.getiterator("keyword"):
                a.keywords.append(node.text.replace(",","，"))
                if "沖縄" in node.text:
                    keys.append(node.text)
                    print(node.tag, node.attrib, node.text)
        
            for node in summ.getiterator("member"):
                print("member")
                print(node.tag, node.attrib, node.text)

                institution = ""
                fullName = ""
                for node2 in node.getiterator("institution"):
                    print(node2.tag, node2.attrib, node2.text)
                    institution = node2.text.replace(",","，")
                for node2 in node.getiterator("fullName"):
                    print(node2.tag, node2.attrib, node2.text)
                    print(a.names)
                    fullName = node2.text.replace(",", "，")
                a.names.append((institution, fullName))

            for node in summ.getiterator("periodOfAward"):
                print(node.tag, node.attrib, node.text)
                print(node.attrib["searchStartFiscalYear"])
                print(node.attrib["searchEndFiscalYear"])
                a.searchStartFiscalYear = node.attrib["searchStartFiscalYear"]
                a.searchEndFiscalYear = node.attrib["searchEndFiscalYear"]
                

            for node in summ.getiterator("overallAwardAmount"):
                print(node.tag, node.attrib, node.text)
            
                for node in summ.getiterator("directCost"):
                    print(node.tag, node.attrib, node.text)

                    a.directCost = node.text

                for node in summ.getiterator("indirectCost"):
                    print(node.tag, node.attrib, node.text)
                    a.indirectCost = node.text

                for node in summ.getiterator("totalCost"):
                    print(node.tag, node.attrib, node.text)
                    a.totalCost = node.text

            print(a)

        print(set(keys))

        return articles


    articles = []
    keys = []

    # articles.extend(load("沖縄_キーワード.xml"))
    # articles.extend(load("沖縄_タイトル.xml"))
    # articles.extend(load("政治学_分野.xml"))
    
    # articles.extend(load("学術創成研究費.xml"))
    # file = "山中伸弥_研究者_kaken.nii.ac.jp_2018-05-17_00-26-56.xml"
    # file = "山口二郎_研究者_kaken.nii.ac.jp_2018-05-17_00-32-13.xml"
    file = "総額1億-5億_期間2000-2017_kaken.nii.ac.jp_2018-05-17_00-51-59.xml"


    articles.extend(load(file))

    ids = []
    articles2 = []
    print(len(articles))
    articles = set(articles)
    print(len(articles))

    names_max = 0
    for a in articles:
        if names_max < len(a.names):
            names_max = len(a.names)
    
    names_header = []
    for i in range(names_max):
        names_header.append(f"研究者{i+1}")
        names_header.append(f"所属{i+1}")
    names_header = ",".join(names_header)


    fields_max = 0
    for a in articles:
        if fields_max < len(a.fields):
            fields_max = len(a.fields)

    fields_header = []
    for i in range(fields_max):
        fields_header.append(f"分野{i+1}")
    fields_header = ",".join(fields_header)

    if fields_header == "":
        fields_header = "分野"

    keywords_max = 0
    for a in articles:
        if keywords_max < len(a.keywords):
            keywords_max = len(a.keywords)

    keywords_header = []
    for i in range(keywords_max):
        keywords_header.append(f"キーワード{i+1}")
    keywords_header = ",".join(keywords_header)

    out = file.replace(".xml", "")
    with open(f'{out}.csv', 'w', errors='ignore') as f:
        f.write(f'id,タイトル,分野,研究者,キーワード,研究期間開始,研究期間終了,直接経費,間接経費,金額合計,{fields_header},{names_header},{keywords_header}\n')

        for a in articles:
            title = a.title

            names = ["" for i in range(names_max * 2)]
            for i in range(names_max):
                try:
                    n = a.names[i]
                    names[i * 2] = n[1]
                    names[i * 2 + 1] = n[0]
                except IndexError:
                    pass
            names = ",".join(names)

            fields = ["" for i in range(fields_max)]
            for i in range(fields_max):
                try:
                    fields[i] = a.fields[i]
                except IndexError:
                    pass
            fields = ",".join(fields)


            keywords = ["" for i in range(keywords_max)]
            for i in range(keywords_max):
                try:
                    keywords[i] = a.keywords[i]
                except IndexError:
                    pass
            keywords = ",".join(keywords)

            f.write(f'{a.id},{title},{a.fields_text()},{a.names_text()},{a.keywords_text()},{a.searchStartFiscalYear},{a.searchEndFiscalYear},{a.directCost},{a.indirectCost},{a.totalCost},{fields},{names},{keywords}\n')

    # print(articles)
    # start_crawle()
