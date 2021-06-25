import asks
import trio
from bs4 import BeautifulSoup
import re
import os
import urllib.parse

limit = trio.CapacityLimiter(2)
BASE_URL = 'https://thetrove.is'
BASE_PATH = os.getcwd() + "/The Trove"

async def mkdir(path):
    d = trio.Path(path)
    if not await d.is_dir():
        await d.mkdir(parents=True)

def mkdir_sync(path):
    if not os.path.exists(path):
        os.makedirs(path)

async def downloader(URL, PATH, linkUrl, DEEP):
    async with limit:    
        r = await asks.get(URL)
    print("S Download " + "           " * (DEEP - 1) + linkUrl) 
    async with await trio.open_file(PATH, 'wb') as file:
        await file.write(r.content)
        print("Downloaded " + "           " * (DEEP - 1) + linkUrl) 

mkdir_sync(BASE_PATH)

async def scrapp(URL,DEEP,limit):
    async with limit:
        page = await asks.get(BASE_URL + "/" + URL)
    soup = BeautifulSoup(page.content, 'html.parser',from_encoding="utf-8")
    soup.encode("utf-8", "ignore")
    results = soup.find(id='list')
    rows = results.findAll("td", {"class": "link"})
#    print("\nRows:               \n")
#    for row in rows:
#        print(row, end = '\n')
    async with trio.open_nursery() as nursery:
        for row in rows:
            link = row.find('a')
            link.encode("utf-8")
            if link.string != "Parent directory/":
                print("row      " + str(row))        
                if "href" in link.attrs:
                    linkUrl = urllib.parse.unquote(link.get('href'))
                    linkUrl = linkUrl.replace('?' , ' ')
                    if re.search("\.\w{1,4}$",linkUrl):
                        d = "/" + URL + "/" + linkUrl
                        if not os.path.exists(BASE_PATH + d):
                            async with limit:
                                nursery.start_soon(downloader, BASE_URL + d, BASE_PATH + d, linkUrl, DEEP)
                                print(("     +     " * DEEP) + linkUrl + " - Queued - ")
                        else:
                            print(("           " * DEEP) + linkUrl + " - Skipped - ")
                    else:
                        await mkdir(BASE_PATH + "/" + URL + "/" + link.string)
                        async with limit:
                            nursery.start_soon(scrapp, URL + "/" + linkUrl, DEEP + 1, limit)
            else:
                print("   Skipping    " + link.string)

#try: 
trio.run(scrapp, "Books", 0, limit)
#except:
#    print("==========            FATAL ERROR            ==========")    
