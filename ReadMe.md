KiCAD BOM Generator
===================

KiCAD comes with a built-in handle for Bill of Materials(BOM) generation. However It does not actually have the full capability of generating a BOM. For that, one needs an external tool. This provides such a tool.

Features
--------
-  Pulls quantity-pricing information from Digikey based on product number
-  Keeps a database of BOMs as well as orders.
-  Includes user login/authentication so projects can be shared in a semi-public way
-  Can download a pre-populated set of Requisition forms for UNL's Physics department workflow as well as a CSV suitable for uploading to digikey to populate a cart directly.

Installation
------------
- Requires Python 3.5
- Simply checkout the project and run the setup script. This will create a virtual environment containing all necessary packages. It will also initialize the database.
- You can startup the webserver by running the "run.py" script. It will likely require you to add a security exemption for the site because the certificate is self-signed. If you would like to avoid this, find yourself a signed certificate and place it in the ssl subdirectory.

How to Use
----------
1.  Add a field to all parts that you wish to appear in the Bill of materials called "Digikey". This must map to a specific part number on Digikey. **Not the Manufacturer part number**
2.  Open the project in KiCAD.
3.  Create a zip archive of the project.
4.  Create an account by clicking on "Register" on the main page.
5.  Upload a new BOM.
6.  When viewing the newly uploaded BOM, click on "Lookup/Refresh Part Information". This will use the part numbers from the schematic to pull additional data from the vendor's website(may take a few minutes).
7.  Create a New Order by clicking the link on the left, filling in the appropriate information, and selecting which BOMs and in what quantity you wish to have the order contain. You can adjust individual part counts in the next step.
8.  On the next page you can edit the quantity of each part you want to order and then hit the "Update Parts Count" button to save your changes. The appropriate price cuts are automatically found and you are notified if no price cut exists for your requested amount.
9.  Finally, when you are happy with the order, you can download either pre-populated Requisition forms for the UNL Physics department, or a CSV that you can upload to Digikey to pre-populate a cart.


To Do
-----
  -  Add support for additional vendors. This mostly just entails writing additional screen-scrapers/api accessors for vendor websites.
  -  Add support for more output formats.
  -  Add ability to refresh Digikey Oauth tokens so the user doesn't need to re-authenticate when the token expires(Every month or so)
  -  Better documentation. :)
