#!/usr/bin/env python3

from collections import namedtuple, defaultdict
from functools import lru_cache, wraps
from os.path import split, join
from decimal import Decimal
import argparse
import urllib
import sys
import re

import requests
from bs4 import BeautifulSoup

DigiPart = namedtuple("DigiPart", ("digikey_part_number",
                                   "url",
                                   "manufacturer_part_number",
                                   "manufacturer",
                                   "description",
                                   "price_breaks",
                                   "misc_data"))

PriceBreak = namedtuple("PriceBreak", ("number", "price_dollars"))
LOCAL_CACHE_FILE = "/home/caleb/.local/digikey_local_cache.sqlite3"
CUTOFF_TIME = 3600*3  # Seconds

HEAD = """
<!DOCTYPE html>
  <head>
    <title>Kicad BOM</title>
    <script src="http://code.jquery.com/jquery-latest.js"></script>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
  </head>
"""

with open(join(sys.path[0], "kicad_bom.css"), "r") as f:
    CSS = f.read()
with open(join(sys.path[0], "kicad_bom.js"), "r") as f:
    JS = f.read()


class disk_cache:
    def __init__(self, cache_file):
        import sqlite3
        self.conn = sqlite3.connect(cache_file)
        self.curs = self.conn.cursor()
        self._create_table()
        # self.db = pickledb.load(cache_file, False)

    def _create_table(self):
        self.curs.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            url TEXT,
            query_date FLOAT,
            page_text TEXT
        ); """)

    def _insert_page(self, url, page_text):
        from time import time
        now = time()
        self.curs.execute("""DELETE FROM pages WHERE url=?;""",
                          (url,))
        self.curs.execute("""INSERT INTO pages VALUES (?, ?, ?);""",
                          (url, now, page_text))

    def _query_page(self, url):
        self.curs.execute("""
        SELECT query_date,page_text FROM pages
            WHERE url=?;""", (url,))
        return self.curs.fetchone()

    def _is_too_old(self, old_time):
        from time import time
        now = time()
        return (now-old_time) > CUTOFF_TIME

    def __call__(self, f):
        @wraps(f)
        def wrapper(arg: str):
            query = self._query_page(arg)
            if not query or self._is_too_old(query[0]):
                data = f(arg)
                self._insert_page(arg, data)
            else:
                data = query[1]
            self.conn.commit()
            return data
        return wrapper


def get_digikey_url(digikey_part_number):
    part_number_url = urllib.parse.quote_plus(digikey_part_number)
    return ("http://www.digikey.com/product-search/en?KeyWords={}" +
            "&WT.z_header=search_go").format(part_number_url)


@disk_cache(LOCAL_CACHE_FILE)
def pull_page(digikey_part_number):
    url = get_digikey_url(digikey_part_number)
    return requests.get(url).text


@lru_cache(maxsize=None)
def scrape_part(digikey_part_number):
    page = pull_page(digikey_part_number)
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
    return DigiPart(digikey_part_number=digikey_part_number,
                    url = get_digikey_url(digikey_part_number),
                    manufacturer_part_number=manufacturer_part_number,
                    manufacturer=manufacturer,
                    description=description,
                    price_breaks=tuple(price_breaks),
                    misc_data=())


def find_unit_price(price_breaks, number):
    price_breaks = sorted(price_breaks, key=lambda x: x.number)
    for i, break_high in enumerate(price_breaks):
        if i == 0 and number < break_high.number:
            return Decimal("NaN")
        break_low = price_breaks[i-1]
        if break_low.number<=number < break_high.number:
            return break_low.price_dollars
    return price_breaks[-1].price_dollars


def get_board_name():
    with open(ARGS.xml_in, 'r') as f:
        soup = BeautifulSoup(f.read(), "lxml")
    source = soup.find("design").source


def get_parts(xml_in):
    with open(xml_in, 'r') as f:
        soup = BeautifulSoup(f.read(), "lxml")
    parts = defaultdict(list)
    for comp in soup.findAll("comp"):
        fields = comp.fields
        if fields:
            digipart = fields.find("field", attrs={"name": "digipart"})
            if digipart:
                digipart = scrape_part(digipart.getText())
                parts[digipart].append(comp.attrs["ref"])
                continue
        print("No digipart for part {}".format(comp.attrs["ref"]))
    return parts


def gen_html_output(title, parts):
    html = [HEAD, CSS]

    html.append("<body>")
    html.append("<h1>{} - Bill of Materials</h1>\n".format(title))
    html.append("<input type=\"text\" id=\"filename\" value=\"MyFile.json\" placeholder=\"filename.json\">")
    html.append("<button onclick=\"downloadFile()\">Create File</button> <span id=\"output\"></span>")

    header = ["<table id=\"parts\">",
              "  <thead>",
              "  <tr>",
              "    <td>#</td>",
              "    <td>Description</td>",
              "    <td>Vendor Part #</td>",
              "    <td>Manufacturer</td>",
              "    <td>Manufacturer Part #</td>",
              "    <td>Board Reference</td>",
              "    <td class=\"num\">Total Used</td>",
              "  </tr>",
              "  </thead>",
              "<tbody>"]
    if(not ARGS.noprice):
        header.insert(10, "    <td class=\"num\">Total Order</td>")
        header.insert(11, "    <td class=\"num\">Unit Price</td>")
        header.insert(12, "    <td class=\"num\">Total Price</td>")
    html.extend(header)
    parts = sorted(parts.items(), key=lambda x: x[1][0])
    total_price = Decimal(0)
    for i, (part, refs) in enumerate(parts):
        if i % 2:
            html.append("<tr class=\"datarow alt\">")
        else:
            html.append("<tr class=\"datarow\">")
        # Left Numbering
        html.append("<td>{}</td>".format(i+1))
        # Part Description
        html.append("<td>{}</td>".format(part.description))
        # Vendor Part Number
        html.append("<td><a href=\"{}\">{}</a></td>".format(part.url,
                                                            part.digikey_part_number))
        # Manufacturer
        html.append("<td>{}</td>".format(part.manufacturer))
        # Manufacturer Part Number
        html.append("<td>{}</td>".format(part.manufacturer_part_number))
        # Board References
        refs.sort(key=lambda x: int(re.search("[0-9]+$",x).group()))
        html.append("<td>{}</td>".format(', '.join(refs)))
        # Number Used
        number_used = len(refs)
        html.append("<td class=\"num\">{}</td>".format(number_used))
        if(not ARGS.noprice):
            # Number Order
            input_ = ("<input type=\"number\" " +
                      "id=\"{id}_input\" " +
                      "value=\"{value}\">").format(id=i, value=number_used)
            html.append("<td class=\"num\">{}</td>".format(input_))
            # Price Breaks w/ current break
            unit_price = find_unit_price(part.price_breaks, number_used)
            price_breaks_txt = ';'.join("{}@{}".format(b.number, b.price_dollars)
                                        for b in part.price_breaks)

            html.append(("<td id=\"{}_priceper\" class=\"num\" title=\"{}\">" +
                        "${:F}</td>").format(i, price_breaks_txt, unit_price))
            gross_price = unit_price*number_used
            total_price += gross_price
            html.append(("<td id=\"{}_price\" " +
                        "class=\"num price\">${:02F}</td>").format(i, gross_price))
        html.append("</tr>")
    if(not ARGS.noprice):
        html.append("<tr>"+"<td></td>"*8 +
                    ("<td>Sum</td><td id=\"pricetot\" class=\"num\">" +
                     "${:F}</td></tr>").format(total_price))
    html.append("</tbody>\n</table>")
    html.append("</body>")
    html.append(JS)

    html = "\n".join(html)
    with open("{}.html".format(ARGS.output), 'w') as f:
        f.write(html)


def main():
    parts = get_parts(ARGS.xml_in)
    title = re.findall("(.*)\.xml$", split(ARGS.xml_in)[1])[0]
    extra_bom = join(split(ARGS.xml_in)[0], "{}_BOMExtra.xml".format(title))
    parts.update(get_parts(extra_bom))
    gen_html_output(title, parts)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    arg = PARSER.add_argument
    arg("xml_in")
    arg("output")
    arg("--no-price", dest="noprice", action="store_true",
        help="include to disable price output, useful for assembly references")
    ARGS = PARSER.parse_args()
    main()
