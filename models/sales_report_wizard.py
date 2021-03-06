from odoo import api, fields, models, _
from pprint import pprint
import calendar
import datetime
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

    invoice_line_ids = fields.Many2many(
        string="Invoice Lines",
        comodel_name="account.invoice.line",
        relation="account_invoice_line_sales_report_detail_rel",
        column1="report_id",
        column2="invoice_line_id"
    )

    def get_idr_currency(self):
        idr_curr = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)
        return idr_curr

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
        pph_line_tax = line.invoice_line_tax_ids.filtered(
            lambda tx: tx.id == default_pph_tax.id)
        return pph_line_tax

    def get_line_ppn(self, line):
        # get default ppn account
        default_sales_tax = self.env.user.company_id.account_sale_tax_id
        line_tax = None
        loopnum = 1
        line_tax = line.invoice_line_tax_ids.filtered(
            lambda tx: tx.id == default_sales_tax.id)

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

        # pprint(filtered_invoice_ids)
        return filtered_invoice_ids

    def get_ppn_idr(self, lines):
        ppn_idr = 0.0
        idr_curr = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)
        usd_curr = self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1)
        default_sales_tax = self.env.user.company_id.account_sale_tax_id

        # get line with idr
        idr_lines = lines.filtered(
            lambda inv: inv.currency_id.id == idr_curr.id)

        print('get ppn idr')
        print('----------------------------------------------------------------')
        for line in idr_lines:
            for tax in line.invoice_line_tax_ids:
                if tax.id == default_sales_tax.id:
                    print(tax.amount / 100 * line.price_subtotal)
                    ppn_idr += tax.amount / 100 * line.price_subtotal


        # get line with usd
        usd_lines = lines.filtered(
            lambda line: line.invoice_id.currency_id.id == usd_curr.id)
        for line in usd_lines:
            for tax in line.invoice_line_tax_ids:
                if tax.id == default_sales_tax.id:
                    tax_line_usd = tax.amount / 100 * line.price_unit * line.quantity
                    tax_line_idr = line.invoice_id.currency_id._convert(
                        tax_line_usd, idr_curr, self.env.user.company_id, line.date_invoice)
                    print(tax_line_idr )
                    ppn_idr += tax_line_idr 
        print('----------------------------------------------------------------')
        # # get all invoices with idr currency
        # idr_invs = invoices.filtered(
        #     lambda inv: inv.currency_id.id == idr_curr.id)
        # for inv in idr_invs:
        #     for line in inv.invoice_line_ids:
        #         for tax in line.invoice_line_tax_ids:
        #             if tax.id == default_sales_tax.id:
        #                 ppn_idr += tax.amount / 100 * line.price_subtotal

        # # get all usd invoices
        # usd_invs = invoices.filtered(
        #     lambda inv: inv.currency_id.id == usd_curr.id)

        # for inv in usd_invs:
        #     for line in inv.invoice_line_ids:
        #         for tax in line.invoice_line_tax_ids:
        #             if tax.id == default_sales_tax.id:
        #                 ppn_usd = tax.amount / 100 * line.price_subtotal
        #                 ppn_idr += usd_curr._convert(ppn_usd, idr_curr,
        #                                              self.env.user.company_id, inv.date_invoice)

        return ppn_idr

    def get_dpp_idr(self, lines):
        dpp_idr = 0.0
        idr_curr = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)
        usd_curr = self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1)

        # get line with idr
        idr_invoices = lines.mapped('invoice_id').filtered(
            lambda inv: inv.currency_id.id == idr_curr.id)
        dpp_idr += sum(idr_invoices.mapped('amount_untaxed'))

        # get line with usd
        # yang ini hasil beda karena cara perhitungan perkaliannya beda
        # usd_invoices = lines.mapped('invoice_id').filtered(lambda inv : inv.currency_id.id == usd_curr.id)
        # for inv in usd_invoices:
        #     dpp_idr += inv.currency_id._convert(inv.amount_untaxed, idr_curr, self.env.user.company_id, inv.date_invoice)

        # pakai cara yang ini
        usd_lines = lines.filtered(
            lambda line: line.invoice_id.currency_id.id == usd_curr.id)
        for line in usd_lines:
            usd_price_unit = line.invoice_id.currency_id._convert(
                line.price_unit, idr_curr, self.env.user.company_id, line.date_invoice)
            dpp_idr += usd_price_unit * line.quantity

        # # get all invoices with idr currency
        # idr_invs = invoices.filtered(
        #     lambda inv: inv.currency_id.id == idr_curr.id)
        # dpp_idr += sum(idr_invs.mapped('amount_untaxed'))

        # # get all usd invoices
        # usd_invs = invoices.filtered(
        #     lambda inv: inv.currency_id.id == usd_curr.id)
        # for inv in usd_invs:
        #     usd_amount_untaxed = inv.amount_untaxed
        #     idr_amount_untaxed = usd_curr._convert(
        #         usd_amount_untaxed, idr_curr, self.env.user.company_id, inv.date_invoice)
        #     dpp_idr += idr_amount_untaxed

        return dpp_idr

    def get_month_name(self, date):
        return calendar.month_name[date.month]

    def get_report_line(self, lines):
        report_line = []
        invoices_mapped = lines.mapped('invoice_id')
        invoice_qty_on_lines = len(invoices_mapped)
        usd_curr = self.env['res.currency'].search(
            [('name', '=', 'USD')], limit=1)
        idr_curr = self.env['res.currency'].search(
            [('name', '=', 'IDR')], limit=1)
        default_sales_tax = self.env.user.company_id.account_sale_tax_id
        default_pph_tax = self.env.user.company_id.pph_23_id
        currency_rate = 0
        fak_dpp_idr = self.get_dpp_idr(lines)
        fak_ppn_idr = self.get_ppn_idr(lines)
        fak_dpp_ppn_idr = fak_dpp_idr + fak_ppn_idr

        if invoice_qty_on_lines > 1:
            inv_year = invoices_mapped[0].date_invoice.year
            inv_month = invoices_mapped[0].date_invoice.month
            last_day_of_month = calendar.monthrange(inv_year, inv_month)[1]
            invoice_date = datetime.date(
                inv_year, inv_month, last_day_of_month)
            
        else:
            invoice_date = invoices_mapped.date_invoice
        
        currency_rate = invoices_mapped[0].currency_id._get_conversion_rate(invoices_mapped[0].currency_id, idr_curr, self.env.user.company_id, invoice_date)

        product_on_lines = lines.mapped('product_id')
        # disticnt product lines
        product_on_lines = list(dict.fromkeys(product_on_lines))

        # print('GET REPORT LINE')
        for prod in product_on_lines:
            filtered_line_by_prod = lines.filtered(
                lambda line: line.product_id.id == prod.id)

            filtered_by_price_unit = filtered_line_by_prod.mapped('price_unit')
            # disticnt by price
            filtered_by_price_unit = list(
                dict.fromkeys(filtered_by_price_unit))

            for prc in filtered_by_price_unit:
                line_by_price = filtered_line_by_prod.filtered(
                    lambda line: line.price_unit == prc)

                # calculate dpp usd
                dpp_usd = 0
                ppn_usd = 0
                dpp_ppn_usd = 0
                harga_idr = 0
                pph_23 = 0

                if line_by_price[0].invoice_id.currency_id.id == usd_curr.id:
                    dpp_usd = sum(line_by_price.mapped('price_subtotal'))
                    for line in line_by_price:
                        ppn_usd += (line.invoice_line_tax_ids.filtered(
                            lambda tx: tx.id == default_sales_tax.id).amount / 100) * (line.price_unit * line.quantity)
                    dpp_ppn_usd = dpp_usd + ppn_usd 
                    harga_idr = line_by_price[0].invoice_id.currency_id._convert(line_by_price[0].price_unit, idr_curr, self.env.user.company_id, invoice_date)
                else:
                    harga_idr = line_by_price[0].price_unit
                
                for line in line_by_price:
                    pph_23 += line.invoice_line_tax_ids.filtered(lambda tx : tx.id == default_pph_tax.id).amount / 100 * harga_idr * line.quantity

                new_line = {
                    'is_usd' : self.is_usd(filtered_line_by_prod[0].invoice_id.currency_id.id),
                    'tanggal': invoice_date,
                    'bulan': calendar.month_name[invoice_date.month],
                    'nomor_faktur': filtered_line_by_prod[0].efaktur_text,
                    'invoice': filtered_line_by_prod[0].invoice_id.number,
                    'partner': filtered_line_by_prod[0].partner_id.name,
                    'product': filtered_line_by_prod[0].product_id.name,
                    'qty': sum(line_by_price.mapped('quantity')),
                    'sat': filtered_line_by_prod[0].uom_id.name,
                    'dpp_usd': dpp_usd,
                    'ppn_usd': ppn_usd,
                    'dpp_ppn_usd': dpp_ppn_usd,
                    'pph': pph_23,
                    'kurs': currency_rate,
                    'harga': harga_idr,
                    'total_harga': harga_idr * sum(line_by_price.mapped('quantity')),
                    'dpp_idr': fak_dpp_idr,
                    'ppn_idr': fak_ppn_idr,
                    'dpp_ppn_idr': fak_dpp_ppn_idr,
                }
                report_line.append(new_line)
            # print('---------------------')

        # for line in report_line:
        #     print(str(line['tanggal']) + '     ' + str(line['bulan']) + '     ' + str(line['nomor_faktur']) + '     ' + str(line['invoice']) + '     ' +
        #           str(line['partner']) + '     ' + str(line['product']
        #                                                 ) + '     ' + str(line['qty']) + '     '
        #           + str(line['sat']) + '     ' + str(line['dpp_usd']
        #                                              ) + '     ' + str(line['ppn_usd']) + '     '
        #           + str(line['dpp_ppn_usd']) + '     ' + str(line['pph']
        #                                                      ) + '     ' + str(line['kurs']) + '     '
        #           + str(line['harga']) + '     ' + str(line['total_harga']
        #                                                ) + '     ' + str(line['dpp_idr']) + '     '
        #           + str(line['ppn_idr']) + '     ' + str(line['dpp_ppn_idr']) + '\n')
        #     print('-----------------------------------------------------------------------------------------------------------------------')

        # print('\n\n###############################')

        # calculate pph_23

        return report_line

    def get_sales_report_detail(self):

        filtered_invoice_ids = {}
        efaktur_line = self.invoice_line_ids.sorted(
            key=lambda line: line.date_invoice).mapped('efaktur_text')
        efaktur_line = list(dict.fromkeys(efaktur_line))

        for fak in efaktur_line:

            line_by_faktur = self.invoice_line_ids.sorted(
                key=lambda line: line.date_invoice).filtered(lambda lin: lin.efaktur_text == fak)

            report_line = self.get_report_line(line_by_faktur)
            
            filtered_invoice_ids[fak] = {
                'faktur': fak,
                'invoice_line': line_by_faktur,
                'report_line': report_line,
            }

        # # get invoice months
        # first_month = self.date_start.month
        # last_month = self.date_to.month
        # usd_curr = self.env['res.currency'].search(
        #     [('name', '=', 'USD')], limit=1)
        # idr_curr = self.env['res.currency'].search(
        #     [('name', '=', 'IDR')], limit=1)

        # filtered_invoice_ids = {}
        # # efakturs = self.invoice_ids.sorted(key=lambda inv : inv.date_invoice).mapped('efaktur_id')
        # efakturs = self.invoice_ids.filtered(lambda inv : inv.efaktur_id)
        # efakturs = efakturs.sorted(key=lambda inv : inv.date_invoice).mapped(lambda x : str(x.prefix_berikat or '') + '.' + str(x.efaktur_id.name or ''))

        # for fak in efakturs:
        #     fak_invoices = self.invoice_ids.filtered(
        #         lambda inv: inv.efaktur_id.id == fak.id).sorted(key=lambda inv : inv.date_invoice)

        #     dpp_idr = self.get_dpp_idr(fak_invoices)
        #     ppn_idr = self.get_ppn_idr(fak_invoices)
        #     dpp_ppn_idr = dpp_idr + ppn_idr

        #     filtered_invoice_ids[fak] = {
        #         'faktur': fak.name,
        #         'invoices': fak_invoices,
        #         'dpp_idr': dpp_idr,
        #         'ppn_idr': ppn_idr,
        #         'dpp_ppn_idr': dpp_ppn_idr,
        #     }

        # pprint(filtered_invoice_ids)

        # # raise UserError('Mohon maaf tidak bisa ..')

        return filtered_invoice_ids

    def action_submit(self):

        all_invoices = self.env['account.invoice'].search(
            ['&', '&', '&',
             ('type', '=', 'out_invoice'),
             ('state', 'in', ['open', 'paid']),
             ('date_invoice', '>=', self.date_start),
             ('date_invoice', '<=', self.date_to),
             ], order="date_invoice asc")

        all_invoices = all_invoices.filtered(
            'efaktur_id').filtered('prefix_berikat')

        all_invoice_lines = self.env['account.invoice.line'].search(
            [('invoice_id', 'in', all_invoices.ids)])
        all_invoice_lines = all_invoice_lines.sorted(
            key=lambda line: line.date_invoice)

        self.write({
            'invoice_ids': [(6, 0, all_invoices.ids)],
            'invoice_line_ids': [(6, 0, all_invoice_lines.ids)],
        })

        # self.get_sales_report_detail()

        # raise UserError('TESTING ERROR')

        # # self.get_filtered_invoice_ids()

        # # show current view
        # self.get_sales_report_detail()
        # return {
        #     'name': 'Sales Report',
        #     'view_type': 'form',
        #     'view_mode': 'form',
        #     'res_model': 'butir.sales.report.wizard',
        #     'type': 'ir.actions.act_window',
        #     'res_id': self.id,
        #     'target': 'current',
        # }

        # # test get report detail
        # # self.get_sales_report_detail()

        # # # return self.env.ref('bt_ketronics_sales_report.action_butir_sales_report').report_action(self)
        # # return self.env.ref('bt_ketronics_sales_report.action_butir_sales_report_detail').report_action(self)
        # return self.env.ref('bt_ketronics_sales_report.action_butir_sales_report_detail_new').report_action(self)

        return self.get_report()

    def get_report(self):
        return self.env.ref('bt_ketronics_sales_report.action_butir_sales_report_detail_new').report_action(self)
