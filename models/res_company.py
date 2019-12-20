from odoo import api, fields, models, _
from odoo.tools.translate import html_translate


class ResCompany(models.Model):
    _inherit = 'res.company'

    pph_23_id = fields.Many2one(
        string='PPH 23',
        comodel_name='account.tax',
        ondelete='cascade',
    )
    
    
    
    
