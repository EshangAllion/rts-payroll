# -*- coding: utf-8 -*-
{
    'name': 'Returned Checks',
    'version': '1.1',
    'category': 'Returned Checks',
    'sequence': 0,
    'summary': 'User able to manage returned Checks',
    'description': """""",
    'website': 'http://www.alliontechnologies.com/',
    'depends': ['bulk_payment'],
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/payment_methods.xml',
        'data/sequence_data.xml',
        'wizard/return_checks_payment_wizard.xml',
        'views/returned_check_view.xml',
    ],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
