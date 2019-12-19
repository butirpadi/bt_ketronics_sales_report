from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_per_pack = fields.Integer('Qty/Pack', default=1)
    pack_weight = fields.Float('Pack Weight')

