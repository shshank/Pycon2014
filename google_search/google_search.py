import requests
from bs4 import BeautifulSoup as BSoup

proxy = ('109.108.78.5', 8080)

user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.122 Safari/537.36'

def get_page(url):
    resp = requests.get(url, headers = {'User-Agent':user_agent})#proxies={'http':'http://222.58.108.10:80', 'https':'https://222.58.108.10:80'})
    if resp.status_code >= 400:
        raise Exception('Bad response from server: Response Code {response_code}'.format(response_code=resp.status_code))
    return resp.content

def get_pagination_urls(page_source):
    urls = []
    soup = BSoup(page_source)
    for i in soup.find_all('a',{'class':'fl'}):
        if i.text.encode('utf-8').isdigit():
            urls.append('http://google.com'+i.get('href'))
    return urls


def parse_page(page_source):
    results = []
    soup = BSoup(page_source)
    search_result_div = soup.find('div', {'id':'search'})
    
    for i in search_result_div.findAll('li', {'class':'g'}):
        link_elem = i.find('h3').find('a')
        if link_elem.get('href').startswith('/images?'):
            continue
        
        title_text = link_elem.text.encode('utf-8')
        
        url = link_elem.get('href').split('/url?q=')[1].split('&')[0]
        url = url.encode('utf-8')
        
        results.append({'title':title_text, 'url':url})
    return results


def search(term):
    url = 'http://google.com/search?q={term}'.format(term=term)
    page_source = get_page(url)
    pagination_urls = get_pagination_urls(page_source)

    results = parse_page(page_source)
    for url in pagination_urls:
        time.sleep('5')
        page_source = get_page(url)
        results += parse_page(page_source)

    return results

for i, v in enumerate(search('pyconindia')):
    v.update({'rank':i+1})
    print v['rank'], v['url'], v['title']




