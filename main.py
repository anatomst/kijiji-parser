import math
import os
from dataclasses import dataclass
from datetime import date, timedelta
from sys import stdout

import requests
from bs4 import BeautifulSoup
from peewee import *


base_url = "https://www.kijiji.ca/b-apartments-condos/city-of-toronto/c37l1700273"

pg_db = PostgresqlDatabase(
    os.environ["DB_NAME"],
    user=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
)


class Ads(Model):
    image = TextField()
    title = CharField()
    date = CharField()
    city = CharField()
    number_of_beds = IntegerField()
    description = TextField()
    price = DecimalField()

    class Meta:
        database = pg_db
        db_table = 'ads_list'


pg_db.connect()
pg_db.create_tables([Ads])


@dataclass
class Ad:
    image: str
    title: str
    date: str
    city: str
    number_of_beds: int
    description: str
    price: float


def get_num_pages(page_soup: BeautifulSoup) -> int:
    num_pages = int(page_soup.select_one(".resultsShowingCount-1707762110").text.split()[-2])
    num_pages = math.ceil(num_pages / 45)
    return num_pages


def parse_single_ad(ad_soup: BeautifulSoup):
    title = ad_soup.select_one("a", {"class": "title"}).text.strip()

    try:
        image = ad_soup.select_one(".image > picture > img")["data-src"]
    except TypeError:
        image = ""

    try:
        date_in_ad = "-".join((ad_soup.select_one(".date-posted").text.split("/")))
        if "ago" in date_in_ad:
            date_in_ad = date.today().strftime("%d-%m-%Y")
        if "yesterday" in date_in_ad:
            date_in_ad = (date.today() - timedelta(days=5)).strftime("%d-%m-%Y")
    except (AttributeError, TypeError):
        date_in_ad = ""

    try:
        city = ad_soup.select_one(".location > span").text.strip().split()[-1]
    except AttributeError:
        city = ""

    try:
        description = ad_soup.select_one(".description").text.strip().replace('\n', ' ')
    except AttributeError:
        description = ""

    try:
        price = float(ad_soup.select_one(".price").text.strip().strip("$").replace(",", ""))
    except ValueError:
        price = 0

    try:
        ad_beds = int(ad_soup.select_one(".bedrooms").text.strip().split()[-1])
    except ValueError:
        ad_beds = 0

    ad = Ads(
        image=image,
        title=title,
        date=date_in_ad,
        city=city,
        number_of_beds=ad_beds,
        description=description,
        price=price,
    )
    ad.save()


def get_single_page_ad(page_soup: BeautifulSoup) -> [Ad]:
    ads = page_soup.find_all("div", attrs={"class": ["search-item", "regular-ad"]})

    return [parse_single_ad(ad_soup) for ad_soup in ads]


def get_items() -> [Ad]:
    response = requests.get(base_url)
    first_page_soup = BeautifulSoup(response.content, "html.parser")

    num_pages = get_num_pages(first_page_soup)

    all_ads = get_single_page_ad(first_page_soup)
    print(num_pages)
    for page_num in range(2, num_pages + 1):
        # print(f"page: {page_num} of {num_pages + 1}")
        stdout.write(f"page: {page_num} of {num_pages + 1} \n")
        page = requests.get(f"https://www.kijiji.ca/b-apartments-condos/city-of-toronto/page-{page_num}/c37l1700273")
        soup = BeautifulSoup(page.content, "html.parser")
        all_ads.extend(get_single_page_ad(soup))
    print(len(all_ads))
    return all_ads


def main():
    get_items()


if __name__ == '__main__':
    main()
