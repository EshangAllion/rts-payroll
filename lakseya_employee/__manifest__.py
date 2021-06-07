{
    'name': 'HR Employee Lakseya',
    'version': '1.0',
    'sequence': 1,
    'author': "Allion Technologies PVT Ltd",
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Employee Lakseya',
    'description': """This module contains employee data""",
    'depends': [
        'hr'
    ],
    'data': [
        'views/inherit_hr_employee.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}