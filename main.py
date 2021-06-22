import requests
from bs4 import BeautifulSoup
import json


def get_page(url):
    user_agent = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Mobile Safari/537.36'
    headers = {'User-Agent': user_agent}
    req = requests.get(url, headers=headers)
    page = BeautifulSoup(req.text, 'html.parser')
    return page


def parse_page(page):
    data_parse = []
    for container in page.find_all("div", {"class": "city-item"}):
        city = container.findChild('h4').text
        for item in container.find_all("div", {"class": "shop-list-item"}):
            obj_parse = {}
            obj_parse['address'] = f"{city}, {item['data-shop-address']}"
            obj_parse['latlon'] = [float(item['data-shop-latitude']), float(item['data-shop-longitude'])]
            obj_parse['name'] = ' '.join(item['data-shop-name'].split(' ')[1:])
            obj_parse['phones'] = str(item['data-shop-phone'])
            obj_parse['working_hours'] = f"{item['data-shop-mode1']} {item['data-shop-mode2']}"
            data_parse.append(obj_parse)
    return data_parse


def get_city_id():
    url = "https://apigate.tui.ru/api/office/cities"
    req = requests.get(url)
    cities_obj = json.loads(req.text)
    cities_id = [city['cityId'] for city in cities_obj['cities']]
    return cities_id


def get_office(cities_id):
    data_parse = []
    for id in cities_id:
        url = f"https://apigate.tui.ru/api/office/list?cityId={id}&subwayId=&hoursFrom=&hoursTo=&serviceIds=all&toBeOpenOnHolidays=false"
        req = requests.get(url)
        office_obj = json.loads(req.text)
        for office in office_obj['offices']:
            obj_parse = {}
            all_phone = []
            work_days = []
            obj_parse['address'] = office['address']
            obj_parse['latlon'] = [float(office['longitude']), float(office['longitude'])]
            obj_parse['name'] = office['name']
            for phones in office['phones']:
                for phone in phones['phone'].split('\n'):
                    all_phone.append(phone.replace(' ', ''))
            obj_parse['phones'] = all_phone
            if not office['hoursOfOperation']['workdays']['isDayOff']:
                 w_day = f"пн - пт {office['hoursOfOperation']['workdays']['startStr']} до {office['hoursOfOperation']['workdays']['endStr']}"
                 work_days.append(w_day)
            if  (office['hoursOfOperation']['saturday']['isDayOff'] == False) and (office['hoursOfOperation']['sunday']['isDayOff'] == False):
                 w_day = f"сб-вс {office['hoursOfOperation']['saturday']['startStr']}-{office['hoursOfOperation']['sunday']['endStr']}"
                 work_days.append(w_day)
            obj_parse['working_hours'] = work_days
            data_parse.append(obj_parse)
    return data_parse


def get_region_id(url):
    regions_obj = []
    req = requests.get(url)
    page = BeautifulSoup(req.text, 'html.parser')
    for li in page.find_all("li"):
        region_obj = {}
        region_obj['region_id'] = li['data-id']
        regions_obj.append(region_obj)
    return regions_obj


def get_cities_regions(regions):
    cities = []
    for region in regions:
        url = f"https://www.tvoyaapteka.ru/bitrix/ajax/modal_geoip.php?action=get_towns&region_id={region['region_id']}"
        req = requests.get(url)
        json_obj = json.loads(req.text)
        if json_obj:
            for obj in json_obj:
                cities.append(obj['ID'])
    return cities


def get_chemists(cities):
    chemists = []
    for city_id in cities:
        url = "https://www.tvoyaapteka.ru/adresa-aptek/"
        cookies = {'BITRIX_SM_S_CITY_ID': str(city_id)}
        req = requests.get(url, cookies=cookies)
        page = BeautifulSoup(req.text, 'html.parser')
        main = page.find('main')
        for div in main.find_all('div', {"class": "apteka_item normal_store"}):
            chemist = {}
            all_span = div.find_all('span')
            chemist['address'] = all_span[1].text
            chemist['latlon'] = [float(div['data-lat']), float(div['data-lon'])]
            chemist['name'] = all_span[0].text
            chemist['working_hours'] = all_span[2].text.replace('\t', '').replace('\n', '')
            chemists.append(chemist)
    return chemists


def return_json(data):
    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False)


if __name__ == '__main__':
    url_0 = "https://www.mebelshara.ru/contacts"
    page = get_page(url_0)
    data_site_0 = parse_page(page)

    cities_id = get_city_id()
    data_site_1 = get_office(cities_id)

    url_1 = "https://www.tvoyaapteka.ru/bitrix/ajax/modal_geoip.php"
    regions = get_region_id(url_1)
    cities = get_cities_regions(regions)
    data_site_2 = get_chemists(cities)

    all_data = {}
    all_data['site1'] = data_site_0
    all_data['site2'] = data_site_1
    all_data['site3'] = data_site_2

    return_json(all_data)
