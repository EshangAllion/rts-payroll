{
    'name': 'Lakseya SMS Gateway',
    'version': '1.1',
    'sequence': 1,
    'author': "Centrics Business Solutions PVT Ltd",
    'website': 'http://www.centrics.cloud/',
    'summary': 'This module contains sms gateway api configurations and integrations',
    'description': """This module contains sms gateway api configurations and integrations""",
    'depends': [
        'lakseya_core', 'sale_management'
    ],
    'external_dependencies': {},
    'data': [
        'security/ir.model.access.csv',
        'data/sms_master_data.xml',
        'views/sms_gateway_config.xml',
        'views/inherit_sale_order.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

