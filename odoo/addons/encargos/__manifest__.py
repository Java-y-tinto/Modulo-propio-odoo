# -*- coding: utf-8 -*-
{
    'name': "Encargos",

    'summary': "Gestión de encargos de obras de arte",

    'description': """
Gestiona encargos de obras de arte de forma automática.Calcula costes de mano de obra y materiales.Gestiona las sesiones de trabajo.
    """,

    'author': "Jaime Román Rueda",
    'website': "https://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale_management','account','calendar'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'security/encargo_security.xml',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

