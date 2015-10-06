#!/usr/bin/env python3

from collections import namedtuple, defaultdict
from functools import lru_cache, wraps
from decimal import Decimal
from os.path import split, join
import argparse
import urllib
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
LOCAL_CACHE_FILE = "/home/caleb/.local/digikey_local_cache.db"

STYLE = """ <style>
#parts {
    font-family: "Trebuchet MS", Arial, Helvetica, sans-serif;
    width: 100%;
    border-collapse: collapse;
}

#parts td, #parts th {
    font-size: 1em;
    border: 1px solid #98bf21;
    padding: 3px 7px 2px 7px;
}

#parts th {
    font-size: 1.1em;
    text-align: left;
    padding-top: 5px;
    padding-bottom: 4px;
    background-color: #A7C942;
    color: #ffffff;
}

#parts thead {
    font-size: 1.1em;
    font-weight: bold;
}

#parts tr.alt td {
    color: #000000;
    background-color: #EAF2D3;
}

#parts td.num {
    text-align: right;
}
</style>
"""
class disk_cache:
    def __init__(self, cache_file):
        import pickledb
        self.db = pickledb.load(cache_file, False)

    def __call__(self, f):
        @wraps(f)
        def wrapper(arg : str):
            data = self.db.get(arg)
            if not data:
                data = f(arg)
                self.db.set(arg, data)
            self.db.dump()
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
    for i, price_break in enumerate(price_breaks):
        if i == 0 and number < price_break.number:
            return Decimal("nan")  # Cannot order so few
        if number >= price_break.number:
            return price_break.price_dollars


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
            else:
                print("No digipart for part {}".format(comp.attrs["ref"]))
        else:
            print("No fields for part {}".format(comp.attrs["ref"]))
    # for part, comps in parts.items():
    #     print("{}   :   {}".format(part.digikey_part_number, comps))
    return parts


def gen_markdown_output(title, parts):
    html = [STYLE]
    html.append("<h1>{} - Bill of Materials</h1>".format(title))

    html.append("\n")
    html.append("<table id=\"parts\">")
    html.append("<thead>\n<tr>")
    html.append("<td>Description</td>")
    html.append("<td>Vendor Part #</td>")
    html.append("<td>Manufacturer</td>")
    html.append("<td>Manufacturer Part #</td>")
    html.append("<td>Board Reference</td>")
    html.append("<td class=\"num\">Total Used</td>")
    html.append("<td class=\"num\">Unit Price</td>")
    html.append("<td class=\"num\">Total Price</td>")
    html.append("</tr>\n</thead>\n<tbody>")
    parts = sorted(parts.items(), key=lambda x: x[1][0])
    total_price = Decimal(0)
    for i, (part, refs) in enumerate(parts):
        if i % 2:
            html.append("<tr>")
        else:
            html.append("<tr class=\"alt\">")
        html.append("<td>{}</td>".format(part.description))
        html.append("<td><a href=\"{}\">{}</a></td>".format(part.url, part.digikey_part_number))
        html.append("<td>{}</td>".format(part.manufacturer))
        html.append("<td>{}</td>".format(part.manufacturer_part_number))
        refs.sort()
        html.append("<td>{}</td>".format(', '.join(refs)))
        number_used = len(refs)
        html.append("<td class=\"num\">{}</td>".format(number_used))
        unit_price = find_unit_price(part.price_breaks, number_used)
        html.append("<td class=\"num\">${:F}</td>".format(unit_price))
        gross_price = unit_price*number_used
        total_price += gross_price
        html.append("<td class=\"num\">${:02F}</td>".format(gross_price))
        html.append("</tr>")
    html.append("<tr>"+"<td></td>"*6+"<td>Sum</td><td class=\"num\">${:F}</td></tr>".format(total_price))
    html.append("</tbody>\n</table>")

    html = "\n".join(html)
    with open("{}.html".format(ARGS.output), 'w') as f:
        f.write(html)


def main():
    parts = get_parts(ARGS.xml_in)
    title = re.findall("(.*)\.xml$", split(ARGS.xml_in)[1])[0]
    extra_bom = join(split(ARGS.xml_in)[0],"{}_BOMExtra.xml".format(title))
    parts.update(get_parts(extra_bom))
    gen_markdown_output(title, parts)


if __name__ == "__main__":
    PARSER = argparse.ArgumentParser()
    PARSER.add_argument("xml_in")
    PARSER.add_argument("output")
    ARGS = PARSER.parse_args()
    main()
