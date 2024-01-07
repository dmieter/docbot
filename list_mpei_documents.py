# %% IMPORTS
from urllib.request import Request, urlopen
from bs4 import BeautifulSoup as bs
import json

# %% GLOBALS

MPEI_URL = "https://mpei.ru/AboutUniverse/OficialInfo/Pages/Orders.aspx"


# %% API FUNCTIONS

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
            date = date_parts[2]+date_parts[1]+date_parts[0]    

        metadata = date + ";" + filename + ";" + name + ";" + href
        if date > "20230901":
            print(metadata)
# %% TEST   
list_all_docs()