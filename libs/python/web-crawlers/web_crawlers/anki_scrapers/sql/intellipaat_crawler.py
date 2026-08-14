from os import getcwd

import requests
from bs4 import BeautifulSoup as soup

page = soup(
    requests.get(
        "https://intellipaat.com/blog/tutorial/sql-tutorial/sql-commands-cheat-sheet/"
    ).content,
    "html.parser",
)
cards = []
for el in page.find_all("tr"):
    td = [e.text for e in el.find_all("td")]
    print(td)
    if len(td) != 3:
        continue
    card_line = (
        f"<b>Statement</b>: {td[0]} | <b>SQL statement</b> used to "
        f"{td[2].lower()}. | {td[1]}"
    )
    cards.append("".join(card_line))

with open(f"{getcwd()}/sql-basic.txt", "w") as file:
    file.writelines([f"{i} \n" for i in cards])
