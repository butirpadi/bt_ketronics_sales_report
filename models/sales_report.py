from odoo import api, fields, models


class ButirSalesReport(models.Model):
    _name = 'butir.sales.report'

    name = fields.Char(string='Name')
