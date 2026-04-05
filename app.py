from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates

import requests
from bs4 import BeautifulSoup
import re
import os

app = FastAPI()

templates = Jinja2Templates(directory="templates")


def fetch_stocks():

    session = requests.Session()

    login_url = "https://www.screener.in/login/"

    response = session.get(login_url)

    soup = BeautifulSoup(response.text, "html.parser")

    csrf = soup.find("input", {"name": "csrfmiddlewaretoken"})["value"]

    payload = {
        "username": os.getenv("SCREENER_USER"),
        "password": os.getenv("SCREENER_PASS"),
        "csrfmiddlewaretoken": csrf
    }


    headers = {
        "Referer": login_url,
        "User-Agent": "Mozilla/5.0"
    }

    session.post(login_url, data=payload, headers=headers)

    base_url = "https://www.screener.in/screen/raw/?sort=&order=&source_id=&query=Price+to+Earning+%3C+30+AND%0D%0AReturn+on+equity+%3E+25+AND%0D%0AEPS+%3E0+AND%0D%0AProfit+growth+%3E+50+AND%0D%0ASales+growth+%3E+50+AND%0D%0ADebt+to+equity+%3C+0.5+AND%0D%0APromoter+holding+%3E+50%0D%0A&page=1"

    response = session.get(base_url)

    soup = BeautifulSoup(response.text, "html.parser")

    page_info = soup.select_one("div[data-page-info]").text

    match = re.search(r'of\s+(\d+)', page_info)

    total_pages = int(match.group(1)) if match else 1

    stocks = []

    for page in range(1, total_pages + 1):

        url = base_url + f"&page={page}"

        response = session.get(url)

        soup = BeautifulSoup(response.text, "html.parser")

        rows = soup.select("tr[data-row-company-id]")

        for row in rows:

            name = row.select_one("td:nth-of-type(2) a").text.strip()
            price = row.select_one("td:nth-of-type(3)").text.strip()

            stocks.append({
                "name": name,
                "price": price
            })

    return stocks


@app.get("/")
def home(request: Request):

    stocks = fetch_stocks()

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"stocks": stocks}
    )


@app.get("/run")
def run_screener():
    stocks = fetch_stocks()
    return stocks

