# -*- coding: utf-8 -*-
{
    'name': "Conector PLEO",
    'summary': """Conector PLEO - ODOO mediante importación de Excel""",
    'author': "Process Control",
    'website': "https://www.processcontrol.es",
    'category': 'Accounting/Accounting',
    'version': '0.1',
    'depends': ['account_accountant', 'hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/res_config_settings_views.xml',
        'views/ticket_views.xml',
        'views/account_account_views.xml',
        'views/res_company_views.xml',
        'views/account_move_views.xml',
        'wizard/procesar_registros_views.xml'
    ],
}
