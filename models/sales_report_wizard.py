from odoo import api, fields, models, _
from pprint import pprint
import calendar
from odoo.exceptions import UserError


class ButirSalesReportWizard(models.TransientModel):
    _name = 'butir.sales.report.wizard'
    _description = 'Sales Report / Laporan penjualan'

    name = fields.Char(string='Name', default="Sales Report")
    date_start = fields.Date(string='Start Date')
    date_to = fields.Date(string='End Date')
    invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        relation='account_invoice_sales_report_rel',
        column1='report_id',
        column2='invoice_id',
        string='Invoices'
    )

    def get_invoice_rate(self, inv):
        idr_curr = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)
        return inv.currency_id._get_conversion_rate(inv.currency_id, idr_curr, self.env.user.company_id, inv.date_invoice)

    def get_total_price(self, line):
        return line.quantity * self.get_unit_price(line)

    def get_unit_price(self, line):
        unit_price = line.price_unit

        if self.is_usd(line.invoice_id.currency_id.id):
            idr_curr = self.env['res.currency'].search(
                [('name', '=', 'IDR')], limit=1)
            unit_price = line.invoice_id.currency_id._convert(
                unit_price, idr_curr, self.env.user.company_id, line.invoice_id.date_invoice)

        return unit_price

    def is_usd(self, currency_id):
        usd_curr = self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1)

        return currency_id == usd_curr.id
    
    def get_line_pph(self, line):
        default_pph_tax = self.env.user.company_id.pph_23_id
        pph_line_tax = line.invoice_line_tax_ids.filtered(lambda tx : tx.id == default_pph_tax.id)
        return pph_line_tax


    def get_line_ppn(self, line):
        # get default ppn account
        default_sales_tax = self.env.user.company_id.account_sale_tax_id
        line_tax = None
        loopnum = 1
        line_tax = line.invoice_line_tax_ids.filtered(lambda tx : tx.id == default_sales_tax.id)
       
        if line_tax:
            pprint(line_tax)

        return line_tax

    def get_filtered_invoice_ids(self):
        print('filtering invoice id')

        # get invoice months
        first_month = self.date_start.month
        last_month = self.date_to.month
        usd_curr = self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1)
        idr_curr = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)

        filtered_invoice_ids = {}

        # self.invoice_ids.filtered(lambda x : x.date_invoice.month >= first_month and x.date_invoice.month <= last_month)

        for x_month in range(first_month, last_month+1, 1):
            all_invoices = self.invoice_ids.filtered(
                lambda inv: inv.date_invoice.month == x_month)

            filtered_invoice_ids[x_month] = {
                'monthname': calendar.month_name[x_month],
                'all_invoices': all_invoices,
                'partner_invoices': {},
                'partner_count': 0,
            }

            partners = filtered_invoice_ids[x_month]['all_invoices'].mapped(
                'partner_id')

            filtered_invoice_ids[x_month]['partner_count'] = len(partners)

            for prn in partners:

                partner_invoices = filtered_invoice_ids[x_month]['all_invoices'].filtered(
                    lambda inv: inv.partner_id.id == prn.id)

                dpp_usd = 0.0
                tax_usd = 0.0
                dpp_idr = 0.0
                tax_idr = 0.0

                # fill sum_untaxed_usd
                print('Partner : ' + prn.name)
                for inv in partner_invoices:
                    if inv.currency_id.id == usd_curr.id:
                        dpp_usd += inv.amount_untaxed
                        tax_usd += inv.amount_tax
                    else:
                        # convert to USD
                        dpp_usd += inv.currency_id._convert(
                            inv.amount_untaxed, usd_curr, self.env.user.company_id, inv.date_invoice)
                        tax_usd += inv.currency_id._convert(
                            inv.amount_tax, usd_curr, self.env.user.company_id, inv.date_invoice)

                    if inv.currency_id.id == idr_curr.id:
                        dpp_idr += inv.amount_untaxed
                        tax_idr += inv.amount_tax
                    else:
                        dpp_idr = inv.currency_id._convert(
                            inv.amount_untaxed, idr_curr, self.env.user.company_id, inv.date_invoice)
                        tax_idr = inv.currency_id._convert(
                            inv.amount_tax, idr_curr, self.env.user.company_id, inv.date_invoice)

                    print(str(inv.amount_untaxed))
                    print(str(inv.amount_tax))

                filtered_invoice_ids[x_month]['partner_invoices'][prn.name] = {
                    'partner_name': prn.name,
                    'invoices': partner_invoices,
                    'dpp_usd': dpp_usd,
                    'tax_usd': tax_usd,
                    'dpp_tax_usd': dpp_usd + tax_usd,
                    'dpp_idr': dpp_idr,
                    'tax_idr': tax_idr,
                    'dpp_tax_idr': dpp_idr + tax_idr,
                }

        pprint(filtered_invoice_ids)
        return filtered_invoice_ids
    
    def get_ppn_idr(self, invoices):
        ppn_idr = 0.0
        idr_curr = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)
        usd_curr = self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1)
        default_sales_tax = self.env.user.company_id.account_sale_tax_id
        
        # get all invoices with idr currency
        idr_invs = invoices.filtered(
            lambda inv: inv.currency_id.id == idr_curr.id)
        for inv in idr_invs:
            for line in inv.invoice_line_ids:
                for tax in line.invoice_line_tax_ids:
                    if tax.id == default_sales_tax.id :
                        ppn_idr += tax.amount / 100 * line.price_subtotal
        
        # get all usd invoices
        usd_invs = invoices.filtered(
            lambda inv: inv.currency_id.id == usd_curr.id)
        
        for inv in usd_invs:
            for line in inv.invoice_line_ids:
                for tax in line.invoice_line_tax_ids:
                    if tax.id == default_sales_tax.id :
                        ppn_usd = tax.amount / 100 * line.price_subtotal        
                        ppn_idr += usd_curr._convert(ppn_usd, idr_curr, self.env.user.company_id, inv.date_invoice)
        
        return ppn_idr


    def get_dpp_idr(self, invoices):
        dpp_idr = 0.0
        idr_curr = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)
        usd_curr = self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1)

        # get all invoices with idr currency
        idr_invs = invoices.filtered(
            lambda inv: inv.currency_id.id == idr_curr.id)
        dpp_idr += sum(idr_invs.mapped('amount_untaxed'))

        # get all usd invoices
        usd_invs = invoices.filtered(
            lambda inv: inv.currency_id.id == usd_curr.id)
        for inv in usd_invs:
            usd_amount_untaxed = inv.amount_untaxed
            idr_amount_untaxed = usd_curr._convert(usd_amount_untaxed, idr_curr, self.env.user.company_id, inv.date_invoice)
            dpp_idr += idr_amount_untaxed
            
        return dpp_idr
    
    def get_month_name(self, date):
        return calendar.month_name[date.month]

    def get_sales_report_detail(self):
        # get invoice months
        first_month = self.date_start.month
        last_month = self.date_to.month
        usd_curr = self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1)
        idr_curr = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)

        filtered_invoice_ids = {}
        efakturs = self.invoice_ids.sorted(key=lambda inv : inv.date_invoice).mapped('efaktur_id')

        for fak in efakturs:
            fak_invoices = self.invoice_ids.filtered(
                lambda inv: inv.efaktur_id.id == fak.id).sorted(key=lambda inv : inv.date_invoice)

            dpp_idr = self.get_dpp_idr(fak_invoices)
            ppn_idr = self.get_ppn_idr(fak_invoices)
            dpp_ppn_idr = dpp_idr + ppn_idr

            filtered_invoice_ids[fak] = {
                'faktur': fak.name,
                'invoices': fak_invoices,
                'dpp_idr': dpp_idr,
                'ppn_idr': ppn_idr,
                'dpp_ppn_idr': dpp_ppn_idr,
            }

        pprint(filtered_invoice_ids)

        # raise UserError('Mohon maaf tidak bisa ..')

        return filtered_invoice_ids

    def action_submit(self):
        all_invoices = self.env['account.invoice'].search(
            ['&', '&', '&',
             ('type', '=', 'out_invoice'),
             ('state', 'in', ['open', 'paid']),
             ('date_invoice', '>=', self.date_start),
             ('date_invoice', '<=', self.date_to),
             ], order="date_invoice asc")

        self.write({
            'invoice_ids': [(6, 0, all_invoices.ids)]
        })

        # self.get_filtered_invoice_ids()

        # # show current view
        # return {
        #     'name': 'Sales Report',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'butir.sales.report.wizard',
        #     'type': 'ir.actions.act_window',
        #     'res_id': self.id,
        #     'target': 'current',
        # }

        # test get report detail
        # self.get_sales_report_detail()

        # return self.env.ref('bt_ketronics_sales_report.action_butir_sales_report').report_action(self)
        return self.env.ref('bt_ketronics_sales_report.action_butir_sales_report_detail').report_action(self)
