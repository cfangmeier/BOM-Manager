KiCAD BOM Generator
===================

KiCAD comes with a built-in handle for Bill of Materials(BOM) generation. However It does not actually have the full capability of generating a BOM. For that, one needs an external script. This provides such a script.

Features
--------
-  Pulls quantity-pricing information from Digikey based on product number
-  Keeps a database of both BOMs as well as orders.
-  Can download a pre-populated set of Requisition forms for UNL's Physics department workflow.


How to Use
----------
1.  Add a field to all parts that you wish to appear in the Bill of materials called "digipart". This must map to a specific part number on Digikey. **Not the Manufacturer part number**
2.  Open the BOM tool in KiCAD's schematic editor.
3.  Add the script that exports the raw bom xml file. To do this, simply create a "Plugin" with a blank "command line" attribute.
4.  Click on "Generate"
4.  Start up the web app by runnint the "run.py" script and going to ``https://localhost:5000/`` in your browser.
5.  Now upload the xml file create in stop 4 and you are in bussiness.


To Do
-----
-  Add support for additional vendors. This mostly just entails writing additional screen-scrapers/api accessors for vendor websites.
-  Add support for more output formats. CSV/Excell is at the top of the list. Automatically populating a cart on Digikey would also be cool.
