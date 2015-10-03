#!/usr/bin/env python3

from collections import namedtuple, defaultdict
from functools import lru_cache
from decimal import Decimal
import argparse
import urllib

import requests
from bs4 import BeautifulSoup
import pickledb

DigiPart = namedtuple("DigiPart", ("digikey_part_number",
                                   "manufacturer_part_number",
                                   "manufacturer",
                                   "description",
                                   "price_breaks",
                                   "misc_data"))
PriceBreak = namedtuple("PriceBreak", ("number", "price_dollars"))
LOCAL_CACHE_FILE = "/home/caleb/.local/digikey_local_cache.db"


@lru_cache(maxsize=None)
def scrape_digikey(digikey_part_number):
    print("Looking in cache for Digikey part {}".format(digikey_part_number))
    local_cache = pickledb.load(LOCAL_CACHE_FILE, False)
    page = local_cache.get(digikey_part_number)
    if not page:
        print("Not in cache, scraping digikey...")
        part_number_url = urllib.parse.quote_plus(digikey_part_number)
        url = ("http://www.digikey.com/product-search/en?KeyWords={}" +
               "&WT.z_header=search_go").format(part_number_url)
        page = requests.get(url).text
        local_cache.set(digikey_part_number, page)
        local_cache.dump()
    else:
        print("Found in cache! Hooray!!")
    soup = BeautifulSoup(page, "lxml")

    manufacturer = soup.find("h2", attrs={"class": "seohtag"}).findChild("span", attrs={"itemprop": "name"}).getText()
    manufacturer_part_number = soup.find("h1", attrs={"class": "seohtag","itemprop": "model"}).getText()
    description = soup.find("td", attrs={"itemprop": "description"}).getText().strip()

    price_breaks = []
    for row in soup.find("td", attrs={"class": "catalog-pricing"}).findAll("tr"):
        cells = [cell.getText() for cell in row.findAll("td")]
        cells = [cell.replace(',', '') for cell in cells]
        if cells:
            price_break = PriceBreak(number=int(cells[0]),
                                     price_dollars=Decimal(cells[1]))
            price_breaks.append(price_break)

    # TODO: Scrape Misc Data

    # print(manufacturer)
    # print(manufacturer_part_number)
    # print(description)
    # print(price_breaks)
    return DigiPart(digikey_part_number=digikey_part_number,
                    manufacturer_part_number=manufacturer_part_number,
                    manufacturer=manufacturer,
                    description=description,
                    price_breaks=tuple(price_breaks),
                    misc_data=())


def main():
    with open(ARGS.xml_in, 'r') as f:
        soup = BeautifulSoup(f.read(), "lxml")
    parts = defaultdict(list)
    for comp in soup.findAll("comp"):
        fields = comp.fields
        if fields:
            digipart = fields.find("field", attrs={"name": "digipart"})
            if digipart:
                digipart = scrape_digikey(digipart.getText())
                parts[digipart].append(comp.attrs["ref"])
            else:
                print("No digipart for part {}".format(comp.attrs["ref"]))
        else:
            print("No fields for part {}".format(comp.attrs["ref"]))
    for part, comps in parts.items():
        print("{}   :   {}".format(part.digikey_part_number, comps))


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("xml_in")
    PARSER.add_argument("output_dir")
    ARGS = PARSER.parse_args()
    main()
