from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line')
    sale_order_id = fields.Many2one('sale.order', string='SO Ref')
    manufacture_order_id = fields.Many2one('mrp.production', string="MO Reff")

    # order_lines = fields.Many2many('sale.order.line', 'sale_order_line_invoice_rel',
    #                                'invoice_line_id', 'order_line_id',  string='Order Lines', copy=False)

    sale_line_ids = fields.Many2many(
        'sale.order.line',
        'sale_order_line_invoice_rel',
        'invoice_line_id', 'order_line_id',
        string='Sales Order Lines', copy=False)
    
    @api.onchange('sale_line_id')
    def _onchange_sale_line_id(self):
        self.product_id = self.sale_line_id.product_id.id
        self.quantity = 1
        self.price_unit = self.sale_line_id.price_unit
        print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
        print('Product : ' + str(self.sale_line_id.product_id.name))
        print('Price Unit : ' + str(self.sale_line_id.price_unit))
        print('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
