# -*- coding: utf-8 -*-
from odoo import http

# class BtKetronicsOd12(http.Controller):
#     @http.route('/bt_ketronics_sales_report/bt_ketronics_sales_report/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bt_ketronics_sales_report/bt_ketronics_sales_report/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bt_ketronics_sales_report.listing', {
#             'root': '/bt_ketronics_sales_report/bt_ketronics_sales_report',
#             'objects': http.request.env['bt_ketronics_sales_report.bt_ketronics_sales_report'].search([]),
#         })

#     @http.route('/bt_ketronics_sales_report/bt_ketronics_sales_report/objects/<model("bt_ketronics_sales_report.bt_ketronics_sales_report"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bt_ketronics_sales_report.object', {
#             'object': obj
#         })