{
    'name': 'Odoo Commissions',
    'version': '1.1',
    'sequence': 1,
    'author': "Centrics Business Solutions PVT Ltd",
    'website': 'http://www.centrics.cloud/',
    'summary': 'This module contains configuration of commissions for employees and departments',
    'description': """This module contains configuration of commissions for employees and departments""",
    'depends': [
        'hr', 'lakseya_core'
    ],
    'external_dependencies': {},
    'data': [
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'views/commission_slab_configuration_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

