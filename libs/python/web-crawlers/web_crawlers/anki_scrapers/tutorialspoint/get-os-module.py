from os import getcwd

import requests
from bs4 import BeautifulSoup as soup

page = soup(
    requests.get("https://tutorialspoint.com/python/os_file_methods.htm").content,
    "html.parser",
)
cards = []
for el in page.find("table", {"class": "table-bordered"}).find_all("tr"):
    td = el.find_all("td")
    if len(td) <= 1:
        continue
    description = td[1].find("p").text.lower()
    link_text = td[1].find("a").text
    cards.append("".join(f"<b>Os method</b> used to {description} | {link_text}"))
    with open(f"{getcwd()}/workbench.txt", "w") as file:
        file.writelines([f"{i} \n" for i in cards])
