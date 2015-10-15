KiCAD BOM Generator
===================

KiCAD comes with a built-in handle for Bill of Materials(BOM) generation. However It does not actually have the full capability of generating a BOM. For that, one needs an external script. This provides such a script.

Features
--------
-  Pulls quantity-pricing information from Digikey based on product number
-  Creates an interactive webpage(a single HTML file) that you can use to adjust order numbers. Usually, you want to order extras. :).
-  Exports a json file that can be further processed to populate order forms. An example is present that populates requisition forms for my department.


How to Use
----------
1.  Add a field to all parts that you wish to appear in the Bill of materials called "digipart". This must map to a specific part number on Digikey. **Not the Manufacturer part number**
2.  Open the BOM tool in KiCAD's schematic editor.
3.  Add the script as a BOM Plugin in KiCAD.
4.  Click on "Generate"
5.  If everything works, it should eventually say "success". Note that this may take some time since it is screen-scraping Digikey for each unique product id. This info is cached on disk so it will run faster in later runs.
6.  There is now a file in the project directory called (ProjectName).html. Open this in a browser and modify any order numbers as needed.
7.  When you are finished, click "Create File" and then on "Download Ready"
8.  Save This json file somewhere and then run it through the final stage to generate whatever output you like. See gen\_po.py for an example on how to do this.


To Do
-----
-  Add support for additional vendors. This mostly just entails writing additional screen-scrapers for vendor websites.
-  Add support for more output formats. CSV/Excell is at the top of the list. Automatically populating a cart on Digikey would also be cool.
