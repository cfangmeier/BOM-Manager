#!/usr/bin/env python3

from collections import namedtuple, defaultdict
from functools import lru_cache, wraps
from os.path import split, join
from decimal import Decimal
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

HEAD = """
<!DOCTYPE html>
  <head>
    <title>Kicad BOM</title>
    <script src="http://code.jquery.com/jquery-latest.js"></script>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
  </head>
"""

CSS = """<style>
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

#parts tr.select td{
    color: #000000;
    background-color: #99CCFF;
}

#parts td.num {
    text-align: right;
}
</style>
"""
JS = """
<script>
function find_price_break(price_breaks, n){
  price_breaks = price_breaks.split(';');
  var num_breaks = price_breaks.length
  for(var i=0; i<num_breaks; i++){
    var break_high = price_breaks[i].split('@');
    var break_high_n = Number(break_high[0]);
    var break_high_price = Number(break_high[1]);
    if(i == 0){
      if(n < break_high_n){
        return Number("NaN");
      }
      else{
        continue;
      }
    }
    var break_low = price_breaks[i-1].split('@');
    var break_low_n = Number(break_low[0]);
    var break_low_price = Number(break_low[1]);
    if(break_low_n<=n && n < break_high_n){
      return break_low_price;
    }
  }
  var break_highest = price_breaks[num_breaks-1].split('@');
  var break_highest_price = Number(break_high[1]);
  return break_highest_price
}

function update_tottot(){
  var prices = $('.price').text().split('$');
  var sum = 0.0;
  for(var i=0; i<prices.length;i++){
    sum += Number(prices[i]);
  }
  $('#pricetot').text('$'+sum.toFixed(6))
}

function cleanUp(a) {
  a.textContent = 'Downloaded';
//  a.dataset.disabled = true;
  $(a).attr('data-disabled', true);

  // Need a small delay for the revokeObjectURL to work properly.
  setTimeout(function() {
    window.URL.revokeObjectURL(a.href);
    $(a).remove()
  }, 1500);
};

function generateFile(){
  console.log("generating file");
  var objs = [];
  $('tr.datarow').each( function(){
    var data = $(this).children();
    var obj = {
      part_number: $(data[2]).text(),
      description: $(data[1]).text(),
      unit_price: $(data[8]).text(),
      total_price: $(data[9]).text(),
      num_order: $(data[7]).children()[0].value,
    };
    objs.push(obj);
  });
//    console.log(JSON.stringify(objs));
    return JSON.stringify(objs);
}

function downloadFile(){
  console.log("preparing file for download");
  window.URL = window.webkitURL || window.URL;

  var prevLink = $('#outlink');
  var output = $('#output');
  if (prevLink) {
    window.URL.revokeObjectURL(prevLink.href);
    output.innerHTML = '';
  }

  var bb = new Blob([generateFile()], {type: "application/json"});

  var a = $('<a id=\\\'outlink\\\'>Download ready</a>');
  a.attr('download',$('#filename').attr('value'));
  a.attr('href',window.URL.createObjectURL(bb));

  a.attr('data-downloadurl', ["application/json", a.download, a.href].join(':'));
  a.draggable = true; // Don't really need, but good practice.
  a.addClass('dragout');

  output.prepend(a);

  a.on('click', function(e) {
    if ('disabled' in this.dataset) {
      return false;
    }

    cleanUp(this);
  });
}

$('input').on('focus', function(){
  $(this).parent().parent().addClass('select');
});

$('input').on('blur', function(){
  $(this).parent().parent().removeClass('select');
});

$('input').on('keypress', function(event) {
  if(event.type == 'keypress'){
    var key = event.charCode || event.keyCode;
    if(key == 13){ // ie. Return
      return;
    }
  }
  $(this).css('background-color', '#FFCCFF');
  });

$('input').on('change keypress', function(event) {
  if(event.type == 'keypress'){
    var key = event.charCode || event.keyCode;
    if(key != 13){ // ie. Not Return
      return;
    }
  }
  $(this).css('background-color', '#FFFFFF');
  var n = Number($(this).val());
  if(Number.isNaN(n)){
    return;
  }
  var id_base = $(this).attr('id').split('_')[0];
  var priceper_field = $('#'+id_base+'_priceper')
  var price_field = $('#'+id_base+'_price')
  var priceper = find_price_break(priceper_field.attr('title'),n);
  var price = priceper*n;
  priceper_field.text('$'+priceper.toFixed(6));
  price_field.text('$'+price.toFixed(6));
  update_tottot();
});
</script>
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

    html.append("\n".join(["<table id=\"parts\">",
                           "  <thead>",
                           "  <tr>",
                           "    <td>#</td>",
                           "    <td>Description</td>",
                           "    <td>Vendor Part #</td>",
                           "    <td>Manufacturer</td>",
                           "    <td>Manufacturer Part #</td>",
                           "    <td>Board Reference</td>",
                           "    <td class=\"num\">Total Used</td>",
                           "    <td class=\"num\">Total Order</td>",
                           "    <td class=\"num\">Unit Price</td>",
                           "    <td class=\"num\">Total Price</td>",
                           "  </tr>",
                           "  </thead>",
                           "<tbody>"]))
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
        refs.sort()
        html.append("<td>{}</td>".format(', '.join(refs)))
        # Number Used
        number_used = len(refs)
        html.append("<td class=\"num\">{}</td>".format(number_used))
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
                    "class=\"num price\">${:02F}</td>").format(i,gross_price))
        html.append("</tr>")
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
    PARSER.add_argument("xml_in")
    PARSER.add_argument("output")
    ARGS = PARSER.parse_args()
    main()
