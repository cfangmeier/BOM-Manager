KiCAD BOM Generator
===================

KiCAD comes with a built-in handle for Bill of Materials(BOM) generation. However It does not actually have the full capability of generating a BOM. For that, one needs an external tool. This provides such a tool.

Features
--------
-  Pulls quantity-pricing information from Digikey based on product number
-  Keeps a database of BOMs as well as orders.
-  Can download a pre-populated set of Requisition forms for UNL's Physics department workflow as well as a CSV suitable for uploading to digikey to populate a cart directly.


How to Use
----------
1.  Add a field to all parts that you wish to appear in the Bill of materials called "digipart". This must map to a specific part number on Digikey. **Not the Manufacturer part number**
2.  Open the BOM tool in KiCAD's schematic editor.
3.  Add the script that exports the raw bom xml file. To do this, simply create a "Plugin" with a blank "command line" attribute.
4.  Click on "Generate"
4.  Start up the web app by running the "run.py" script and going to ``https://localhost:5000/`` in your browser.
5.  Now upload the xml file you created in stop 4 and you are in buissiness.


To Do
-----
  -  Add support for additional vendors. This mostly just entails writing additional screen-scrapers/api accessors for vendor websites.
  -  Add support for more output formats.
  -  Add ability to refresh Digikey Oauth tokens so the user doesn't need to re-authenticate when the token expires(every few days)
