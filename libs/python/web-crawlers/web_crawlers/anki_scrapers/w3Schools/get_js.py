from os import getcwd, mkdir

import requests
from bs4 import BeautifulSoup as soup


def make_folder(name):
    try:
        mkdir(f"{getcwd()}/{name}")
    except FileExistsError:
        pass


home_page = soup(
    requests.get("https://www.w3schools.com/jsref/default.asp").content, "html.parser"
)
url_arr = [
    [{"url": a["href"], "title": a.text} for a in div.find_all("a")]
    for div in home_page.find_all("div", {"class": "refcont"})
]
title_arr = [
    "Built-in Objects",
    "Window",
    "DOM",
    "Web Api",
]
make_folder("workbench/")

for idx, t in enumerate(title_arr):
    title = "".join(t.split())
    make_folder(f"workbench/{title}")
    for url in url_arr[idx]:
        print(f"getting the content for {url['title']}")
        cards = []
        try:
            res = soup(
                requests.get(f"https://www.w3schools.com/jsref/{url['url']}").content,
                "html.parser",
            )
        except Exception:
            url_arr[idx]["url"].append(url)
            continue
        for table in res.find_all("table", {"class": "ws-table-all"}):
            bold = ""
            for tr in table.find_all("tr"):
                if len(tr.find_all("th")) > 0:
                    section_title = tr.find("th").text.lower()
                    bold = f"<b>{url['title'].capitalize()} {section_title}</b>"
                elif tr.find("a"):
                    ref = soup(
                        requests.get(
                            f"https://www.w3schools.com/jsref/{tr.find('a')['href']}"
                        ).content,
                        "html.parser",
                    )
                    b = [i.text for i in tr.find_all("td")]
                    try:
                        back_extended = (
                            ref.find("h2", text="Syntax")
                            .findNext()
                            .findChild("div")
                            .decode_contents()
                            .strip()
                        )
                        front = f"{bold}: {back_extended}"
                    except Exception as e:
                        back_extended = ""
                        front = f"{bold}: {b[0].lower()}"
                        print(f"Error at {ref.find('h2', text='Syntax')}: {e}")
                    back_basic = f"{bold} that {b[1].lower()}."
                    additional_info = ""
                    version = ""
                    try:
                        example = (
                            ref.find("div", {"class": "w3-example"})
                            .find("div", {"class": "w3-code"})
                            .decode_contents()
                            .strip()
                        )
                    except AttributeError:
                        example = ""
                    card_line = (
                        f"{front} | {back_basic} | {additional_info} | "
                        f"{back_extended} | {example} | {version}"
                    )
                    cards.append(" ".join(card_line.splitlines()))
        with open(
            f"{getcwd()}/workbench/{title}/{''.join(url['title'].split(' '))}.txt", "w"
        ) as file:
            file.writelines([f"{i} \n" for i in cards])
