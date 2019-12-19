# -*- coding: utf-8 -*-
from odoo import http

# class BtKetronicsOd12(http.Controller):
#     @http.route('/bt_ketronics_od12/bt_ketronics_od12/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bt_ketronics_od12/bt_ketronics_od12/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('bt_ketronics_od12.listing', {
#             'root': '/bt_ketronics_od12/bt_ketronics_od12',
#             'objects': http.request.env['bt_ketronics_od12.bt_ketronics_od12'].search([]),
#         })

#     @http.route('/bt_ketronics_od12/bt_ketronics_od12/objects/<model("bt_ketronics_od12.bt_ketronics_od12"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bt_ketronics_od12.object', {
#             'object': obj
#         })