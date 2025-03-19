# filename: link.py
# author:   basilguo@163.com
# version:  v1.0.2
# date:     Oct. 28, 2022
# usage:    python link.py [username]
import requests
import os
import sys
import re
from bs4 import BeautifulSoup

def browser(url):
    login_page = 'https://dashboard.cpolar.com/login'
    try:
        session = requests.Session()
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.0.0 Safari/537.36'
        }

        params = {
            'login': '',
            'password': '',
            'csrf_token': ''
        }
        resp = session.post(login_page, params, headers=headers)
        resp = session.get(url, headers=headers)
        data = resp.content.decode('UTF-8')
        return data
    except Exception as e:
        print(str(e))

def parse_html(html):
    ret = []
    css_rule = '#dashboard > div > div:nth-child(2) > div.span9 > table > tbody > tr'
    soup = BeautifulSoup(html, features="html.parser")
    items = soup.select(css_rule)
    for item in items:
        # print(item)
        # print('--------------------------------')
        # print(item.find('td').text)
        # print(item.find('th').text)
        # print('--------------------------------')
        data = {
            'title':item.find('td').text,
            "link":item.find('th').text,
        }
        ret.append(data)
    return ret

def main():
    url = 'https://dashboard.cpolar.com/status'
    html = browser(url)
    raw_sshs = parse_html(html)
    print(raw_sshs)

    for info in raw_sshs:
        print('-------------------------------- ')
        print(info)
        print('-------------------------------- ')
        if(info['title'] == 'ssh'):
            link = info['link'].split('//')[1]
            address = link.split(':')[0]
            port = link.split(':')[1]
            print(address)
            print(port)
            # os.system('sudo  ssh %s@%s -p %s' % ('king', address, port))
        # exit()

if __name__ == '__main__':
    main()