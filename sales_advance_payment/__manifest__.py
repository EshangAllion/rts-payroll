# -*- coding: utf-8 -*-
{
    'name': 'Sales Advance Payment',
    'version': '1.1',
    'category': 'Sales Advance Payment',
    'sequence': 0,
    'summary': 'User able to manage Sales Advance Payment',
    'description': """""",
    'website': 'http://www.alliontechnologies.com/',
    'depends': ['payment', 'bulk_payment'],
    'data': [
        'wizard/sale_advance_payment_view.xml',
        'reports/job_slip.xml',
        'views/inherit_sale_order.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
