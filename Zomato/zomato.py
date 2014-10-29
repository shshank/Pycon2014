import requests
from bs4 import BeautifulSoup
from urllib import quote
import os

HEADERS = {'user-agent':'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.67 Safari/537.36'}
HEADERS = {}

class Zomato(object):
    def __init__(self, url):
        self.url = url.split('/?')[0].split('#')[0].split('info')[0]
        print self.url
        self.soup = self.get_soup()
        self.res_id = self.get_res_id()


    def get_soup(self):
        resp = requests.get(self.url, headers=HEADERS)
        return BeautifulSoup(resp.content)

    def get_res_id(self):
        soup = self.soup
        meta_tag = soup.find('meta', {'name':'twitter:app:url:iphone'})
        return meta_tag.get('content').strip('zomato://r/').strip()


    def get_basics(self):
        soup = self.soup
        metas = soup.findAll('meta')
        metas = filter(lambda x: x.get('property') and 'og:' in x.get('property'), metas)
        data = {}
        for item in metas:
            if not 'locale' in item.get('property'):
                data[item.get('property').strip('og:')] = item.get('content')
        data['url'] = data['url'].split('?ztype')[0]
        return data

    def get_photos(self, user_type='zomato', max_count=100):
        import json
        total_count = 0
        photos = []
        zomato_filter = lambda photo: photo['user_id'] == 1
        no_zomato_filter = lambda photo: photo['user_id'] !=1

        user_filter = zomato_filter if user_type=='zomato' else no_zomato_filter if user_type=='nozomato' else lambda photo:True
        
        soup = self.soup.find('div', {'class':'res-photo-thumbnails'})
        photo_hrefs = soup.findAll('a', {'class':'res-info-thumbs'})
        if not photo_hrefs:
            return {'total_count':total_count, 'zomato_count':0, 'photos':photos, 'current_count':len(photos)}
        
        #first_photo_id = photo_hrefs[0].get('data-photo_id')
        first_photo_id = 'r_MTg5MzQ5NTQ5Mj'
        url = 'http://www.zomato.com/php/resPhotoData?photo_id={photo_id}&type=res&res_id={res_id}&offset=0'
        photos_resp = requests.get(url.format(photo_id=first_photo_id, res_id=self.res_id))
        photos_resp_json = json.loads(photos_resp.content)
        new_photos = [item for item in photos_resp_json['data'] if user_filter(item)]

        photos += new_photos
        
        total_count += photos_resp_json['total_photos_count']
        
        max_count = min(total_count, max_count)
        
        if photos:
            while len(photos)<max_count or not new_photos:
                photo_id = photos[-1]['image_id']

                photos_resp = requests.get(url.format(photo_id=photo_id, res_id=self.res_id))
                photos_resp_json = json.loads(photos_resp.content)

                new_photos = [item for item in photos_resp_json['data'] if user_filter]
                photos += new_photos

        return {'total_count':total_count, 'photos':photos[:max_count], 'current_count':len(photos[:max_count])}


    def get_menu(self):
        url = os.path.join(self.url,'menu?page={page_num}')
        page_num = 1
        resp = requests.get(url.format(page_num=page_num))
        if resp.status_code == 404:
            return []
        
        soup = BeautifulSoup(resp.content)
        get_pic_url = lambda x: x.find('div', {'id':'menu-image'}).find('img').get('src')
        try:
            menus = [get_pic_url(soup)]
        except:
            return []
        
        while True:
            page_num +=1
            resp = requests.get(url.format(page_num=page_num))
            if not resp.status_code == 404:
                soup = BeautifulSoup(resp.content)
                try:
                    menus += [get_pic_url(soup)]
                except:
                    break
            break

        return menus

    def get_highlights(self):
        highlight_div = self.soup.find('div', {'class':'res-info-highlights column alpha'})
        feature_divs = highlight_div.findAll('div', {'class':'res-info-feature-text'})
        return [item.contents[0].strip() for item in feature_divs]

    def get_phone(self):
        telephone_span = self.soup.find('span', {'class':'tel'})
        spans = telephone_span.findAll('span')
        if not spans:
            return []
        return [item.contents[0].strip() for item in spans]


    def get_reviews(self):
        all_itemprops = filter(lambda item:item.get('itemprop')=='description', self.soup.findAll())
        reviews = [item.contents[1].contents for item in all_itemprops]
        return [''.join([item for item in review if type(item).__name__=='NavigableString']).strip() for review in reviews]


    def get_cover(self):
        soup = self.soup
        div = soup.find('div', {'class':'res-imagery le-header res-imagery-dark imagery item-to-hide-parent'})
        if div:
            return div.get('style').split('url("')[1].split()[0].strip('"')
        return None


    def get_location(self):
        soup = self.soup
        coordinates = soup.find('div', {'id':'res-map-canvas'}).contents[1].get('data-original').split('https://maps.googleapis.com/maps/api/staticmap?center=')[1].split('&')[0].split(',')
        all_itemprops = filter(lambda item:item.get('itemprop'), soup.findAll())
        for item in all_itemprops:
                if item.get('itemprop') == 'addressLocality':
                    locality = item.contents[0].strip()
                if item.get('itemprop') == 'addressCountry':
                    country = item.contents[0].strip()
                if item.get('itemprop') == 'address':
                    address = item.contents[0].strip()
                    city = item.contents[2].strip()
        return {'city':city,
                'locality':locality,
                'country':country,
                'coordinates':coordinates,
                'address':address
                }


    def get_rating(self):
        soup = self.soup
        rating_div = soup.find('div', {'itemprop':'ratingValue'})
        rating = rating_div.contents[0].strip()
        rating_count = soup.find('span', {'itemprop':'ratingCount'}).contents[0].strip()
        return {
                'rating':rating,
                'rating_count':rating_count
                }


    def get_cuisines(self):
        soup = self.soup
        all_itemprops = filter(lambda item:item.get('itemprop')=='servesCuisine', soup.findAll())
        return [item.contents[0].strip() for item in all_itemprops]


    def get_cost(self):
        soup = self.soup
        all_itemprops = filter(lambda item:item.get('itemprop')=='priceRange', soup.findAll())
        itemprop = all_itemprops[0]
        price_value = [int(i.strip()) for i in itemprop.contents[0].contents if type(i).__name__=='NavigableString'][0]
        price_content = itemprop.contents[0].find('span').contents[0].strip().replace('.', '')
        description = itemprop.contents[1].strip()
        if len(itemprop.contents)>2:
            message = itemprop.contents[2].contents[0].strip()
        else:
            message=''
        return {'price_value':price_value,
                'price_currency':price_content,
                'description':description,
                'message':message
                }

if __name__ == '__main__':
    urls = [
            'http://www.zomato.com/ncr/the-kathis-vasant-kunj-delhi',
            'http://www.zomato.com/ncr/monkey-bar-vasant-kunj-delhi/'
            ]
    for url in urls:
        z = Zomato(url)
        #print z.get_basics()
        #print z.get_res_id()
        #print z.get_photos(user_type='zomato', max_count=10)
        #print z.get_menu()
        #print z.get_reviews()
        #print z.get_cover()
        #print z.get_location()
        #print z.get_rating()
        #print z.get_cuisines()
        #print z.get_cost()
        print z.get_highlights()
        print z.get_phone()