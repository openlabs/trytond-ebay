# -*- coding: utf-8 -*-
"""
    test_views

    Tests views and depends

    :copyright: (c) 2013 by Openlabs Technologies & Consulting (P) Limited
    :license: GPLv3, see LICENSE for more details.
"""
from trytond.pool import Pool
from .ebay import SellerAccount


def register():
    "Register classes with pool"
    Pool.register(
        SellerAccount,
        module='ebay', type_='model'
    )