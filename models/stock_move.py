from odoo import api, fields, models
import math 


class StockMove(models.Model):
    _inherit = 'stock.move'

    pack_qty = fields.Float(
        'Packing', compute='_compute_pack_weight', store=True)
    gross_weight = fields.Float(
        'Gross Weight', compute='_compute_pack_weight', store=True, default=0.00)
    net_weight = fields.Float(
        'Net Weight', compute="_compute_pack_weight", store=True, default=0.00)

    manufacture_order_id = fields.Many2one('mrp.production', string='M/Order')

    product_code = fields.Char(
        'Product Code', related="product_id.default_code")

    move_manufacture_type = fields.Selection([
        ('in_house', 'In House'),
        ('subcon', 'Subconract'),
    ], string='Manufacture Type', compute="_compute_manufacture_type", store=True)

    # order_id = fields.Many2one('sale.order', related="sale_line_id.order_id", string="SO Reff")
    # client_order_ref = fields.Char(compute='_compute_client_order_ref', string='Customer Reff', store=True)

    # @api.multi
    # @api.depends('sale_line_id')
    # def _compute_client_order_ref(self):
    #     for rec in self:
    #         if rec.sale_line_id:
    #             rec.client_order_ref = rec.sale_line_id.order_id.client_order_ref

    sale_order_id = fields.Many2one('sale.order', string='SO')

    # @api.onchange('sale_line_id')
    # def _onchange_sale_line(self):
    #     self.sale_order_id = self.sale_line_id.order_id.id

    @api.depends('sale_line_id')
    def _compute_manufacture_type(self):
        for rec in self:
            rec.move_manufacture_type = rec.sale_line_id.order_id.manufacture_type
            if rec.picking_id:
                rec.picking_id.pick_manufacture_type = rec.move_manufacture_type

    @api.depends('quantity_done')
    def _compute_pack_weight(self):
        for rec in self:
            rec.pack_qty = math.ceil(rec.quantity_done / rec.product_id.qty_per_pack) if rec.quantity_done > 0 else 0
            rec.net_weight = rec.quantity_done * rec.product_id.weight
            rec.gross_weight = rec.net_weight + (rec.product_id.pack_weight * rec.pack_qty)
