{
    'name': 'Validate Sales Returned Checks',
    'version': '1.0',
    'category': 'Sales',
    'sequence': 0,
    'author': 'Allion Technologies PVT Ltd',
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Reduce steps to create invoice, auto create invoice from SO and validate it.',
    'description': """auto create invoice from sale order when sale order confirm""",
    'depends': ['sale', 'returned_checks'],
    'data': [
        'views/sale_inherit_view.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
