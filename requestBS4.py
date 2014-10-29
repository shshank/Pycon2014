import requests
from bs4 import BeautifulSoup as BSoup

resp = requests.get('http://google.com/search?q=pyconindia')
if resp.status_code >= 400:
	raise Exception('Bad response from server')

soup = BSoup(resp.content)
search_result_div = soup.find('div', {'id':'search'})

for i in search_result_div.findAll('li', {'class':'g'}):
	link_elem = i.find('h3').find('a')
	title_text = link_elem.text
	if link_elem.get('href').startswith('/images?'):
		continue
	url = link_elem.get('href').split('/url?q=')[1].split('&')[0]
	print title_text, '\n', url, '\n\n'
