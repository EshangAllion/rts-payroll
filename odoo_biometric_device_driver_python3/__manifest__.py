{
    'name': 'Odoo Biometric Integration With Python3',
    'version': '1.1',
    'category': 'Human Resources',
    'sequence': 1,
    'author': "Allion Technologies PVT Ltd",
    'website': 'http://www.alliontechnologies.com/',
    'summary': 'Middleware for Biometric device and Odoo',
    'description': """Sync all the HR data with the biometric device and get attendance detail from the device through Odoo HR Attendance module""",
    'depends': [
        'hr',
        'resource',
        'hr_attendance'
    ],
    'external_dependencies': {},
    'data': [
        'security/ir.model.access.csv',
        'security/record_rule.xml',
        'views/biometric_attendance_log_view.xml',
        'views/biometic_device_config_view.xml',
        'views/hr_attendance_view.xml',
        'wizard/biometric_device_view.xml',
        'wizard/attendance_calc_wizard_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
}

