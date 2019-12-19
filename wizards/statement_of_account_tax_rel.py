from odoo import api, fields, models


class StatementOfAccountTax(models.Model):
    _name = 'statement.of.account.tax.rel'
    _description = 'RELATION BETWEEN statement_of_account AND account_tax'

    statement_id = fields.Many2one(
        comodel_name='statement.of.account',
        string='Statement'
    )

    tax_id = fields.Many2one(
        comodel_name='account.tax',
        string='Tax'
    )

    account_invoice_line_id = fields.Many2one(
        comodel_name='account.invoice.line',
        string='Account Invoice Line'
    )

    tax_amount = fields.Float('Tax Amount')
