# -*- coding: utf-8 -*-
{
    'name': "Ketronics Sales Report",

    'summary': """
        PT. Ketronics Indonesia Custom Module Sales Report""",

    'description': """
        PT. Ketronics Indonesia Custom Module Sales Report
    """,

    'author': "butirpadi@gmail.com",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'account', 'sale_management', 'mrp', 'vit_efaktur'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # views
        'views/res_company_view.xml',
        # 'views/account_invoice_view.xml',
        # 'views/statement_of_account_view.xml',
        # 'views/product_template_view.xml',
        # 'views/stock_picking_view.xml',
        # 'views/sale_order_view.xml',
        'views/sales_report_wizard_view.xml',
        'views/account_invoice_lines.xml',
        # 'views/templates.xml',
        # reports
        # 'reports/statement_of_account_report.xml',
        # 'reports/customer_account_invoice_report.xml',
        # 'reports/packing_list_report.xml',
        'reports/action_report.xml',
        'reports/sales_report.xml',
        'reports/sales_report_detail.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'application': True,
    'installable': True
}
