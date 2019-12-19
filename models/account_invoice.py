from odoo import api, fields, models
from pprint import pprint


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sale_order_ids = fields.Many2many(
        comodel_name='sale.order',
        relation='account_invoice_sale_order_rel',
        string='Auto-Complete'
    )

    manufacture_type = fields.Selection([
        ('in_house', 'In House'),
        ('subcon', 'Subconract'),
    ], string='Manufacture Type')

    authorized_name = fields.Char('Authorized by,')

    def action_invoice_open(self):

        # super(SaleOrder, self).action_cancel()
        res = super(AccountInvoice, self).action_invoice_open()
        # add invoice line to sale order
        self.add_invoice_lines_to_sale_order()

        return res

    def add_invoice_lines_to_sale_order(self):
        if len(self.sale_order_ids) > 0:
            print('.')
            pprint(self.invoice_line_ids)
            for inv_line in self.invoice_line_ids:
                pprint(inv_line)
                # inv_line.sale_order_ids = (4,inv_line.sale_line_id.id)
                inv_line.sale_line_id.invoice_lines = [(4, inv_line.id)]

    @api.onchange('sale_order_ids')
    def _onchange_invoice_sale_order(self):
        new_lines = self.env['account.invoice.line']
        for so in self.sale_order_ids:
            # if not any(line.sale_order_id == so.id for line in self.invoice_line_ids):
            # if not is_exist:
            for line in so.order_line:
                taxes = line.tax_id
                invoice_line_tax_ids = line.order_id.fiscal_position_id.map_tax(
                    taxes, line.product_id, line.order_id.partner_id)
                invoice_line = self.env['account.invoice.line']
                date = self.date or self.date_invoice
                print('*****************************************')
                print('sale order line id : ' + str(line.id))
                print('*****************************************')
                data = {
                    'sale_line_id': line.id,
                    'sale_order_id': so.id,
                    'name': line.order_id.name + ': ' + line.name,
                    'origin': line.order_id.name,
                    'uom_id': line.product_uom.id,
                    'product_id': line.product_id.id,
                    'account_id': invoice_line.with_context({'journal_id': self.journal_id.id, 'type': 'in_invoice'})._default_account(),
                    'price_unit': line.order_id.currency_id._convert(
                        line.price_unit, self.currency_id, line.company_id, date or fields.Date.today(), round=False),
                    'quantity': line.product_uom_qty,
                    'discount': 0.0,
                    # 'account_analytic_id': line.account_analytic_id.id,
                    # 'analytic_tag_ids': line.analytic_tag_ids.ids,
                    'invoice_line_tax_ids': invoice_line_tax_ids.ids
                }
                account = invoice_line.get_invoice_line_account(
                    'in_invoice', line.product_id, line.order_id.fiscal_position_id, self.env.user.company_id)
                if account:
                    data['account_id'] = account.id
                new_line = new_lines.new(data)
                new_line._set_additional_fields(self)
                new_lines += new_line

        self.invoice_line_ids = new_lines
