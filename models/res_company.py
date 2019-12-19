from odoo import api, fields, models, _
from odoo.tools.translate import html_translate


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_footer_note = fields.Text(string='Invoice Footer')
    invoice_footer_html_note = fields.Html('Invoice Note', translate=html_translate)
    # npwp_num = fields.Char('NPWP')
    fax = fields.Char('Fax')
    
    
    
