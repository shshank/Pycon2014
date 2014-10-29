# coding=utf-8

import requests
import pickle
import os
import json
import time
import traceback
from selenium import webdriver
from bs4 import BeautifulSoup as BS4

import config

br = webdriver.PhantomJS()

def restart():
    global br
    try:
        br.close()
    except:
       br = webdriver.PhantomJS()
       login()

def login():
    br.get('http://facebook.com')
    if os.path.exists('cookies.pkl'):
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            br.add_cookie(cookie)

    else:
        try:
            form = br.find_element_by_id('login_form')
            email_input = br.find_element_by_id('email')
            pass_input = br.find_element_by_id('pass')
            email_input.send_keys(config.facebook_username)
            pass_input.send_keys(config.facebook_password)
            form.submit()
            br.find_element_by_id('checkpointSubmitButton').click()
            pickle.dump( br.get_cookies() , open("cookies.pkl","wb"))
        except Exception as e:
            print traceback.format_exc(e)
            br.save_screenshot('error.png')
            print "Check error.png file for screenshot of browser"
        br.get('http://facebook.com')




def search(name, location_id, pages=10):
    pages = min(100, pages)
    url = "https://www.facebook.com/search/str/{search_term}/users-named/{location_id}/residents/present/intersect"
    br.get(url.format(search_term=name, location_id=location_id))
    time.sleep(2)
    for i in xrange(pages):
        old_content_length = len(br.find_elements_by_class_name('_1zf'))
        br.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        while old_content_length == len(br.find_elements_by_class_name('_1zf')):
            print old_content_length, len(br.find_elements_by_class_name('_1zf'))
            time.sleep(1)
        print i

    source = br.page_source
    return parse_search_page(source)

def get_graph(url):
    graph_data = requests.get(url.replace('www', 'graph')).content
    return json.loads(graph_data)

def parse_search_page(source):
    soup = BS4(source)
    divs = soup.find_all('div', {'class':'_1zf'})
    data = []
    for div in divs:
        link_elem = div.find('div', {'data-bt':'{"ct":"title"}'}).find('a')
        print link_elem['href'].split('?')
        url = link_elem['href']
        
        image_link = soup.find('a', {'href':url, 'data-bt':'{"ct":"image"}'})
        image_url = image_link.find('img')['src']
        
        stripped_url = link_elem['href'].split('?')[0]
        name = link_elem.getText()

        for i in div.find('div', {'data-bt':'{"ct":"snippets"}'}).find_all('div', {'class':'_52eh'}):
            line = i.getText()
            if line.startswith('Lives in'):
                cities = line.lstrip('Lives in ').split(unicode(' · From ', 'utf-8'))

        user_data = {"url":stripped_url, "name":name, "profile_pic":image_url, "cities":cities, "graph_data":get_graph(url)}
        for k, v in user_data.items():
            print k, v
        print ''
        data.append(user_data)
    return data


if __name__ == '__main__':
    login()
    data = search(name='gupta',location_id=config.locations['mumbai'], pages=10)

    print data

