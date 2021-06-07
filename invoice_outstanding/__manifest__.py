{
    'name': 'Invoice Outstanding',
    'version': '1.0',
    'category': 'Sales',
    'sequence': 0,
    'author': 'Allion Technologies PVT Ltd',
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Reduce steps to create invoice, auto create invoice from SO and validate it.',
    'description': """auto create invoice from sale order when sale order confirm""",
    'depends': ['sale', 'account', 'returned_checks', 'bulk_payment', 'deposited_funds'],
    'data': [
        'views/account_invoice_view.xml',
        'views/partner_inherit_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
