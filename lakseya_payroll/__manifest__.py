{
    'name': 'HR Payroll Lakseya',
    'version': '1.0',
    'sequence': 1,
    'author': "Allion Technologies PVT Ltd",
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Employee Recruitment',
    'description': """This module contains employee recruitment process""",
    'depends': [
        'hr_payroll', 'hr'
    ],
    'data': [
        'data/input_types_data.xml',
        'security/ir.model.access.csv',
        'views/global_leaves.xml',
        'views/inherit_hr_contract.xml',
        'reports/inherit_payroll_report_actions.xml',
        'reports/salary_slip.xml',
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}