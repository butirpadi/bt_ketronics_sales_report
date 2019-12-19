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
            all_invoices = self.invoice_ids.filtered(lambda inv: inv.date_invoice.month == x_month)

            filtered_invoice_ids[x_month] = {
                'monthname': calendar.month_name[x_month],
                'all_invoices': all_invoices,
                'partner_invoices': {},
                'partner_count' : 0,
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

        # for month in filtered_invoice_ids:
        #     partners = filtered_invoice_ids[month]['all_invoices'].mapped('partner_id')
        #     for prn in partners:
        #         filtered_invoice_ids[month]['partner_invoices'][prn.name] = {
        #             'partner_name' : prn.name,
        #             'invoices' : filtered_invoice_ids[month]['all_invoices'].filtered(lambda inv: inv.partner_id.id == prn.id)
        #         }
            # print('Partner in ' + filtered_invoice_ids[month]['monthname'] + ' : ')
            # for prn in partners:
            #     print(prn.name)
            # print('-----------------------------')
            # print('\n')

        # # TEST CONTENT
        # pprint(filtered_invoice_ids)

        # # STOP FOR TESTING
        # raise UserError('STOP RUNNING FOR TESTING')

        # print('Get invoice months')
        # for inv in self.invoice_ids:
        #     # monthname = calendar.month_name[inv.date_invoice.month]
        #     invmonth = inv.date_invoice.month
        #     if invmonth not in filtered_invoice_ids.keys():
        #         filtered_invoice_ids[invmonth] = {
        #             'monthname' : calendar.month_name[invmonth],
        #             'invoice' : {}
        #         }

        #         # for inv_2 in self.invoice_ids:
        #         #     if inv_2.date_invoice.month == invmonth:
        #         #         if inv_2.partner_id.name not in filtered_invoice_ids[invmonth].keys():
        #         #             # filtered_invoice_ids[inv.date_invoice.month][inv_2.partner_id.name] = self.invoice_ids.filtered(lambda x : x.date_invoice.month == inv.date_invoice.month and x.partner_id.id == inv_2.partner_id.id )
        #         #             usd_curr = self.env['res.currency'].search(
        #         #                 [('name', '=', 'USD')], limit=1)
        #         #             idr_curr = self.env['res.currency'].search(
        #         #                 [('name', '=', 'IDR')], limit=1)

        #         #             print('Currency ID : ')
        #         #             print(usd_curr)
        #         #             print(idr_curr)

        #         #             sum_untaxed_usd = sum(self.invoice_ids.filtered(lambda x: x.date_invoice.month == inv.date_invoice.month and x.partner_id.id ==
        #         #                                                     inv_2.partner_id.id and x.currency_id.id == usd_curr.id).mapped('amount_untaxed'))
        #         #             sum_ppn_usd = sum(self.invoice_ids.filtered(lambda x: x.date_invoice.month == inv.date_invoice.month and x.partner_id.id ==
        #         #                                                     inv_2.partner_id.id and x.currency_id.id == usd_curr.id).mapped('amount_tax'))
        #         #             sum_untaxed_idr = sum(self.invoice_ids.filtered(lambda x: x.date_invoice.month == inv.date_invoice.month and x.partner_id.id ==
        #         #                                                     inv_2.partner_id.id and x.currency_id.id == idr_curr.id).mapped('amount_untaxed'))
        #         #             sum_ppn_idr = sum(self.invoice_ids.filtered(lambda x: x.date_invoice.month == inv.date_invoice.month and x.partner_id.id ==
        #         #                                                     inv_2.partner_id.id and x.currency_id.id == idr_curr.id).mapped('amount_tax'))

        #         #             total_usd = sum_usd + idr_curr._convert()
        #         #             idr_curr._convert(sum_untaxed_idr, usd_curr, self.company_id, self.date_invoice or fields.Date.today())
        #         #             currency_id._convert(self.amount_untaxed, self.company_id.currency_id, self.company_id, self.date_invoice or fields.Date.today())

        #         #             dpp_usd = sum(self.invoice_ids.filtered(lambda x: x.date_invoice.month == inv.date_invoice.month and x.partner_id.id ==
        #         #                                                     inv_2.partner_id.id and x.currency_id.id == usd_curr.id).mapped('amount_untaxed'))
        #         #             ppn_usd = sum(self.invoice_ids.filtered(lambda x: x.date_invoice.month == inv.date_invoice.month and x.partner_id.id ==
        #         #                                                     inv_2.partner_id.id and x.currency_id.id == usd_curr.id).mapped('amount_tax'))
        #         #             dpp_idr = sum(self.invoice_ids.filtered(lambda x: x.date_invoice.month == inv.date_invoice.month and x.partner_id.id ==
        #         #                                                     inv_2.partner_id.id and x.currency_id.id == idr_curr.id).mapped('amount_untaxed'))
        #         #             ppn_idr = sum(self.invoice_ids.filtered(lambda x: x.date_invoice.month == inv.date_invoice.month and x.partner_id.id ==
        #         #                                                     inv_2.partner_id.id and x.currency_id.id == idr_curr.id).mapped('amount_tax'))

        #         #             filtered_invoice_ids[invmonth][inv_2.partner_id.name] = {
        #         #                 'dpp_usd': dpp_usd,
        #         #                 'ppn_usd': ppn_usd,
        #         #                 'dpp_ppn_usd': dpp_usd + ppn_usd,
        #         #                 'dpp_idr': dpp_idr,
        #         #                 'ppn_idr': ppn_idr,
        #         #                 'dpp_ppn_idr': dpp_idr + ppn_idr,
        #         #                 'invoice_ids': self.invoice_ids.filtered(lambda x: x.date_invoice.month == inv.date_invoice.month and x.partner_id.id == inv_2.partner_id.id)
        #         #             }

        #         #             # filtered_invoice_ids[inv.date_invoice.month]['name'] = inv_2.partner_id.name
        #         #             # filtered_invoice_ids[inv.date_invoice.month]['dpp_usd'] = dpp_usd
        #         #             # filtered_invoice_ids[inv.date_invoice.month]['ppn_usd'] = inv_2.partner_id.name
        #         #             # filtered_invoice_ids[inv.date_invoice.month]['dpp_ppn_usd'] = inv_2.partner_id.name
        #         #             # filtered_invoice_ids[inv.date_invoice.month]['dpp_idr'] = dpp_idr
        #         #             # filtered_invoice_ids[inv.date_invoice.month]['ppn_idr'] = inv_2.partner_id.name
        #         #             # filtered_invoice_ids[inv.date_invoice.month]['dpp_ppn_idr'] = inv_2.partner_id.name

        #         # if inv.partner_id.name not in filtered_invoice_ids[inv.date_invoice.month].keys():
        #         #     filtered_invoice_ids[inv.date_invoice.month] = inv.partner_id.name

        #     # if filtered_invoice_ids[inv.date_invoice.month]:
        #     #     if len(filtered_invoice_ids[inv.date_invoice.month]) > 0:
        #     #         # if inv.partner_id.name not in filtered_invoice_ids[inv.date_invoice.month]:
        #     #         #     filtered_invoice_ids[inv.date_invoice.month].append(inv.partner_id.name)
        #     #         print('add partner name')
        #     #     else:
        #     #         filtered_invoice_ids[inv.date_invoice.month] = []
        #     #         filtered_invoice_ids[inv.date_invoice.month].append(inv.partner_id.name)

        pprint(filtered_invoice_ids)
        return filtered_invoice_ids

    def action_submit(self):
        all_invoices = self.env['account.invoice'].search(
            ['&', '&', '&',
             ('type', '=', 'out_invoice'),
             ('state', 'in', ['open', 'paid']),
             ('date_invoice', '>=', self.date_start),
             ('date_invoice', '<=', self.date_to),
             ])

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

        return self.env.ref('bt_ketronics_sales_report.action_butir_sales_report').report_action(self)
