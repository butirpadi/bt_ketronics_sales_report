from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    prefix_berikat = fields.Char(
        related='invoice_id.prefix_berikat', string='Prefix NSFP', store=True)
    efaktur_id = fields.Many2one(
        'vit.efaktur', related='invoice_id.efaktur_id', string='Nomor eFaktur', store=True)
    date_invoice = fields.Date(
        related='invoice_id.date_invoice',
        store=True)
    efaktur_text = fields.Char(
        string="eFaktur", compute="_compute_efaktur_text", store=True)

    @api.depends('efaktur_id', 'prefix_berikat')
    def _compute_efaktur_text(self):
        for rec in self:
            if rec.prefix_berikat != '' and rec.efaktur_id is not None:
                rec.efaktur_text = rec.prefix_berikat + '.' + rec.efaktur_id.name
            elif rec.efaktur_id:
                rec.efaktur_text = rec.efaktur_id.name
            elif rec.prefix_berikat:
                rec.efaktur_text = None
            
