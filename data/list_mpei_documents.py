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

def retrieve_all_docs(from_date):
    req = Request(MPEI_URL)
    response = urlopen(req).read()

    docs = []
    
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

        div_desc = link.find('div', class_ = "description")
        if div_desc:
            desc = div_desc.text

        expire_date = date_add_days(date, 120) # expires in 4 months by default
        if date > from_date:
            docs.append((date, expire_date, filename, name ,href, desc))


    return docs

def list_all_docs(from_date):
    links_set = set()
    docs = retrieve_all_docs(from_date)

    for date, expire_date, filename, name ,href, desc in docs:
        metadata = date.replace(";", "") + ";" + expire_date.replace(";", "") + ";" + filename.replace(";", "") + ";" + name.replace(";", "") + ";" + href.replace(";", "") + ";" + desc.replace(";", "").replace("\r\n", " ")
        links_set.add(metadata)

    links_list = sorted(list(links_set), reverse=False)
    for link in links_list:
        print(link)    




# %% TEST   
list_all_docs("2024-01-01")