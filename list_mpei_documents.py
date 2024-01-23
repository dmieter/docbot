# %% IMPORTS
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as bs
from datetime import datetime
from datetime import timedelta

# %% GLOBALS

MPEI_URL = "https://mpei.ru/AboutUniverse/OficialInfo/Pages/Orders.aspx"


# %% API FUNCTIONS

def date_add_days(date_str, days):
    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
    date_plus = date_obj + timedelta(days)
    return date_plus.strftime('%Y-%m-%d')

def list_all_docs():
    req = Request(MPEI_URL)
    response = urlopen(req).read()

    soup = bs(response, features='html.parser')
    links = soup.find_all('div', class_ = "link-item")
    print(len(links))
    for link in links:
        a = link.find("a")
        if a:
            href = a['href']
            name = a.text
            href_parts = href.split("/")
            filename = href_parts[-1]
            

        div_date = link.find('div', class_ = "listdate")
        if div_date:
            date = div_date.text
            date_parts = date.split('.')
            date = date_parts[2]+"-"+date_parts[1]+"-"+date_parts[0]

        expire_date = date_add_days(date, 120) # expires in 4 monthes by default
        metadata = date + ";" + expire_date + ";" + filename + ";" + name + ";" + href
        if date > "2023-12-01":
            print(metadata)
# %% TEST   
list_all_docs()