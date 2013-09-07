# -*- coding: utf-8 -*-
"""
    party

    Party

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.model import fields
from trytond.pool import PoolMeta, Pool
from trytond.transaction import Transaction


__all__ = ['Party', 'Address']
__metaclass__ = PoolMeta


class Party:
    "Party"
    __name__ = 'party.party'

    ebay_user_id = fields.Char(
        'eBay User ID',
        help="This is global and unique ID given to a user across whole ebay. "
        "Warning: Editing this might result in duplication of parties on next"
        " import"
    )

    @classmethod
    def __setup__(cls):
        """
        Setup the class before adding to pool
        """
        super(Party, cls).__setup__()
        cls._error_messages.update({
            'account_not_found': 'eBay Account does not exist in context',
            'invalid_party': 'eBay user ID for party should be unique!',
        })

    @classmethod
    def validate(cls, parties):
        super(Party, cls).validate(parties)
        for party in parties:
            party.check_ebay_user_id()

    def check_ebay_user_id(self):
        "Check the eBay User ID for duplicates"
        if self.ebay_user_id and len(
            self.search([('ebay_user_id', '=', self.ebay_user_id)])
        ) > 1:
            self.raise_user_error('invalid_party', (self.ebay_user_id,))

    @classmethod
    def find_or_create_using_ebay_id(cls, ebay_user_id):
        """
        This method tries to find the party with the ebay ID first and
        if not found it will fetch the info from ebay and create a new
        party with the data from ebay using create_using_ebay_data

        :param ebay_id: User ID sent by ebay
        :return: Active record of record created/found
        """
        SellerAccount = Pool().get('ebay.seller.account')

        ebay_parties = cls.search([
            ('ebay_user_id', '=', ebay_user_id),
        ])

        if ebay_parties:
            return ebay_parties[0]

        seller_account = SellerAccount(
            Transaction().context.get('ebay_seller_account')
        )

        api = seller_account.get_trading_api()

        user_data = api.execute(
            'GetUser', {'UserID': ebay_user_id, 'DetailLevel': 'ReturnAll'}
        ).response_dict()

        return cls.create_using_ebay_data(user_data)

    @classmethod
    def create_using_ebay_data(cls, ebay_data):
        """
        Creates record of customer values sent by ebay

        :param ebay_data: Dictionary of values for customer sent by ebay
        :return: Active record of record created
        """
        party, = cls.create([{
            'name': ebay_data['User']['RegistrationAddress']['Name']['value'],
            'ebay_user_id': ebay_data['User']['UserID']['value'],
            'contact_mechanisms': [
                ('create', [{
                    'email': ebay_data['User']['Email']['value']
                }])
            ]
        }])

        return party


class Address:
    "Address"
    __name__ = 'party.address'

    def match_with_ebay_data(self, address_data):
        """
        Match the current address with the address_record.
        Match all the fields of the address, i.e., streets, city, subdivision
        and country. For any deviation in any field, returns False.

        :param address_data: Dictionary of address data from ebay
        :return: True if address matches else False
        """
        Country = Pool().get('country.country')
        Subdivision = Pool().get('country.subdivision')

        # Find country and subdivision based on ebay data
        country, = Country.search([
            ('code', '=', address_data['Country']['value'])
        ], limit=1)
        subdivision = Subdivision.search_using_ebay_state(
            address_data['StateOrProvince']['value'], country
        )

        return all([
            self.name == address_data['Name']['value'],
            self.street == address_data['Street']['value'],
            self.zip == address_data['PostalCode']['value'],
            self.city == address_data['CityName']['value'],
            self.country == country,
            self.subdivision == subdivision,
        ])

    @classmethod
    def find_or_create_for_party_using_ebay_data(cls, party, address_data):
        """
        Look for the address in tryton corresponding to the address_record.
        If found, return the same else create a new one and return that.

        :param party: Party active record
        :param address_data: Dictionary of address data from ebay
        :return: Active record of address created/found
        """
        for address in party.addresses:
            if address.match_with_ebay_data(address_data):
                break

        else:
            address = cls.create_for_party_using_ebay_data(
                party, address_data
            )

        return address

    @classmethod
    def create_for_party_using_ebay_data(cls, party, address_data):
        """
        Create address from the address record given and link it to the
        party.

        :param party: Party active record
        :param address_data: Dictionary of address data from ebay
        :return: Active record of created address
        """
        Country = Pool().get('country.country')
        Subdivision = Pool().get('country.subdivision')
        ContactMechanism = Pool().get('party.contact_mechanism')

        country, = Country.search([
            ('code', '=', address_data['Country']['value'])
        ], limit=1)
        subdivision = Subdivision.search_using_ebay_state(
            address_data['StateOrProvince']['value'], country
        )

        address, = cls.create([{
            'party': party.id,
            'name': address_data['Name']['value'],
            'street': address_data['Street']['value'],
            'zip': address_data['PostalCode']['value'],
            'city': address_data['CityName']['value'],
            'country': country.id,
            'subdivision': subdivision.id,
        }])

        # Create phone as contact mechanism
        if not ContactMechanism.search([
            ('party', '=', party.id),
            ('type', 'in', ['phone', 'mobile']),
            ('value', '=', address_data['Phone']['value']),
        ]):
            ContactMechanism.create([{
                'party': party.id,
                'type': 'phone',
                'value': address_data['Phone']['value'],
            }])

        return address
