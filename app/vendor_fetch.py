import json
from datetime import datetime, timedelta
from collections import defaultdict
from urllib.parse import quote_plus
from flask import session, redirect, flash, url_for
from app import app, oauth, db
from .models import VendorPart, Part


class Digikey():
    form_info = defaultdict(str)
    form_info['long_name'] = 'Digikey inc.'
    form_info['addr_line1'] = '701 Brooks Avenue South'
    form_info['addr_line2'] = 'Thief River Falls, MN 56701 USA'
    form_info['phone'] = '218-681-6674'
    form_info['fax'] = '218-681-3380'
    form_info['website'] = 'www.digikey.com'

    def __init__(self):
        self.oauth = oauth.remote_app('Digikey',
                                      app_key='DIGIKEY',
                                      request_token_url=None,)
        self.oauth.tokengetter(self.tokengetter)
        self.name = 'Digikey'

    def login(self):
        """ User Authorization.

        Redirect the user/resource owner to the OAuth provider (i.e. Digikey)
        using an URL with a few key OAuth parameters.
        """
        session['login_vendor'] = 'Digikey'
        return self.oauth.authorize(callback=url_for('oauth_callback',
                                                     _external=True))

    def callback(self):
        """ Authorization Callback

        Gets the authorization response from the redirect url. and uses
        it to get the session token.
        """
        resp = self.oauth.authorized_response()
        if resp is None:
            flash('Request for authorization denied. :(', category='warning')
        else:
            flash('You logged in successfully.', category='success')
            now = datetime.now()
            lifetime = timedelta(seconds=int(resp['expires_in']))
            session['Digikey_token'] = resp['access_token']
            session['Digikey_token_refresh'] = resp['refresh_token']
            session['Digikey_token_expires'] = now+lifetime
        return redirect(url_for('login'))

    @property
    def logged_on(self):
        """ Checks if logged on

        Returns True is the session contains a non-expired token,
        false otherwise.
        """
        expired = session.get('Digikey_token_expires')
        if expired is None or expired < datetime.now():
            return False
        return 'Digikey_token' in session

    def tokengetter(self):
        return session['Digikey_token'], ''

    def part_from_response(self, response):
        vendorpart = VendorPart()
        vendorpart.json = json.dumps(response)
        vendorpart.vendor = 'Digikey'
        vendorpart.vendor_part_number = response['vendor_part_number']
        vendorpart.fetch_timestamp = datetime.now()
        vendorpart.price_breaks = response['Pricing']
        vendorpart.url = response['PartDetailUrl']
        manufacturer = response['ManufacturerName']['Text']
        mpn = response['ManufacturerPartNumber']
        query = Part.query
        query = query.filter(Part.manufacturer == manufacturer,
                             Part.manufacturer_part_number == mpn)
        part = query.first()
        if part is None:
            part = Part()
            part.manufacturer = manufacturer
            part.manufacturer_part_number = mpn
            part.short_description = response['ProductDescription']
            try:
                for media_link in response['MediaLinks']:
                    if media_link['MediaType'] == 'Product Photos':
                        part.image_url = media_link['Thumbnail']
                        break
                raise ValueError('Missing Image URL')
            except (ValueError, KeyError):
                part.image_url = url_for('static', filename='missing_part.png')
        vendorpart.part = part
        return vendorpart

    def query(self, bompart):
        """ Query API for part info

        Takes a BOMPart object and uses the lookup_id field to
        query the Digikey API for more part info. Returns a
        newly created VendorPart. Will also create a Part
        if necessary. Returns None if problems were encountered.
        """
        if not self.logged_on:
            return None
        headers = {
            'accept': "*/*",
            'x-ibm-client-id': self.oauth.consumer_key,
            'X-DIGIKEY-Locale-Language': 'en',
            'X-DIGIKEY-Locale-Site': 'us',
            'X-DIGIKEY-Locale-Currency': 'usd',
            'X-DIGIKEY-Locale-ShipToCountry': 'us',
            'content-type': "application/json",
            }
        data = {'PartNumber': quote_plus(bompart.lookup_id),
                'Quantity': 1,
                'PartPreference': 'CT'}

        try:
            resp = self.oauth.post('search',
                                   format='json',
                                   data=data,
                                   headers=headers)
        except json.decoder.JSONDecodeError as e:
            flash(('Error Looking up part {}! '
                   'JSONDecodeError {}').format(bompart.lookup_id, e),
                  category='warning')
            return None
        if resp.status != 200:
            flash(('Error Looking up part {}! '
                   'API returned {}').format(bompart.lookup_id, resp.status),
                  category='warning')
            return None
        part_raw = resp.data['Parts'][0]
        part_raw['vendor'] = 'Digikey'
        part_raw['vendor_part_number'] = bompart.lookup_id
        vendorpart = self.part_from_response(part_raw)
        bompart.part = vendorpart.part
        db.session.add(vendorpart.part)
        db.session.add(bompart)
        db.session.add(vendorpart)
        db.session.commit()
        return vendorpart

vendors = {'Digikey': Digikey()}


@app.route("/oauth_callback", methods=["GET"])
def oauth_callback():
    """ Retrieve an access token.

    The user has been redirected back from the provider to your registered
    callback URL. With this redirection comes an authorization code included
    in the redirect URL. We will use that to obtain an access token.
    """

    vendor = vendors[session['login_vendor']]
    return vendor.callback()


def populate_parts(bom):
    for bompart in bom.bomparts:
        query = VendorPart.query
        query = query.filter(VendorPart.vendor == bompart.lookup_source,
                             VendorPart.vendor_part_number == bompart.lookup_id)
        vendorpart = query.first()
        if vendorpart is not None:
            bompart.part = vendorpart.part
            db.session.add(bompart)
            db.session.commit()
        elif bompart.lookup_source is not None:
            vendors[bompart.lookup_source].query(bompart)
