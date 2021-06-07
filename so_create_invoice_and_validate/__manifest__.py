{
    'name': 'Auto Create Invoice From SO And Validate',
    'version': '1.0',
    'category': 'Sales',
    'sequence': 0,
    'author': 'Allion Technologies PVT Ltd',
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Reduce steps to create invoice, auto create invoice from SO and validate it.',
    'description': """auto create invoice from sale order when sale order confirm""",
    'depends': ['sale_management'],
    'data': [
        'views/inherit_res_company_view.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
