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

def retrieve_recent_docs(number = 100, from_date = '2024-01-01'):
    req = Request(MPEI_URL)
    response = urlopen(req).read()

    docs = set()
    
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
            docs.add((date, expire_date, filename, name ,href, desc))


    retrieve_num = min(len(docs), number)
    
    return sorted(list(docs), reverse=True)[:retrieve_num]

def list_all_docs(from_date):
    docs = retrieve_recent_docs(from_date = from_date, number = 1000)

    for date, expire_date, filename, name ,href, desc in docs:
        metadata = date.replace(";", "") + ";" + expire_date.replace(";", "") + ";" + filename.replace(";", "") + ";" + name.replace(";", "") + ";" + href.replace(";", "") + ";" + desc.replace(";", "").replace("\r\n", " ")
        print(metadata)  




# %% TEST   
list_all_docs("2024-02-14")