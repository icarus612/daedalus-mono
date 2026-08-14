from os import getcwd

import requests
from bs4 import BeautifulSoup as soup

page = soup(
    requests.get("https://www.w3schools.com/sql/sql_ref_keywords.asp").content,
    "html.parser",
)
cards = []

for el in page.find_all("tr"):
    td = [e.text for e in el.find_all("td")]
    if len(td) != 2:
        continue
    statement = td[1][0].lower() + td[1][1:]
    card_line = f"<b>Statement</b>: {td[0]} | <b>SQL statement</b> used to {statement}."
    cards.append("".join(card_line))


with open(f"{getcwd()}/sql-basic.txt", "w") as file:
    file.writelines([f"{x} \n" for x in cards])
