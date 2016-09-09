# -*- coding: utf-8 -*-
{
    'name': 'Recurring Documents Plus',
    'version': '0.1',
    'category': 'Customization',
    'summary': '',
    'description': """
            Subscription Extended Module for Odoo V9
    """,
    'author' : 'ZedeS Technologies',
    'website' : 'http://www.zedestech.com',
    'depends': ['subscription', 'sale'],
    'data': [],
    'demo': [],
    'test': [],
    'update_xml': [
        'views/subscription_view.xml',
        'views/sale_template_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True,
    'auto_install': False
}