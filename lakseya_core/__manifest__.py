{
    'name': 'Lakseya Core',
    'version': '1.1',
    'sequence': 1,
    'author': "Centrics Business Solutions PVT Ltd",
    'website': 'http://www.centrics.cloud/',
    'summary': 'This module contains all the basic functions relevant to Lakseya',
    'description': """This module contains all the basic functions relevant to Lakseya""",
    'depends': [
        'sale_management', 'product', 'hr', 'sale'
    ],
    'external_dependencies': {},
    'data': [
        'security/security_groups.xml',
        'security/ir.model.access.csv',
        'views/main_menuitem.xml',
        'views/inherit_product.xml',
        'views/inherit_sales_order.xml',
        'views/inherit_res_partner_view.xml',
        'views/inherit_account_payment.xml',
        'wizards/service_log_wizard_view.xml'
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

