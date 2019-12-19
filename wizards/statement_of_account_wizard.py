from odoo import api, fields, models, _
from pprint import pprint
import xlsxwriter
import base64
# from datetime import datetime
# from dateutil import parser


class StatementOfAccount(models.TransientModel):
    _name = 'statement.of.account'
    _description = 'Statement of Account Wizard'

    name = fields.Char(string='Name', default='New')
    partner_id = fields.Many2one(
        'res.partner', string='Customer', domain=[('customer', '=', 1)])
    end_of_date = fields.Date('End Date')
    invoice_ids = fields.Many2many(
        comodel_name='account.invoice',
        relation='statement_of_account_invoice_rel',
        column1='statement_id',
        column2='invoice_id',
        string='Account Invoice'
    )
    print_date = fields.Date(string='Print Date', default=fields.Date.today())

    currency_id = fields.Many2one('res.currency',  string="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.id)
    total_untaxed = fields.Monetary(
        string='Untaxed Amount', currency_field='currency_id')
    total_tax = fields.Monetary(string='Tax', currency_field='currency_id')
    total_with_tax = fields.Monetary(
        string='Total', currency_field='currency_id')
    total_quantity = fields.Float('Quantity')

    carrier_xlsx_document = fields.Binary(string='Excel File')
    carrier_xlsx_document_name = fields.Char(string='Doc Name', default='0')

    # tax_ids = fields.One2many(
    #     comodel_name='statement.of.account.tax.rel',
    #     inverse_name='statement_id',
    #     string='Tax',
    #     )

    def get_tax_ids(self):
        tax_ids = {}
        print('master tax')
        print('-------------------------------------')
        for invoice in self.invoice_ids:
            for tax in invoice.tax_line_ids:
                if tax.tax_id in tax_ids:
                    tax_ids[tax.tax_id] = tax_ids[tax.tax_id] + \
                        tax.amount_total
                else:
                    tax_ids[tax.tax_id] = tax.amount_total
        return tax_ids

    # def compute_tax(self):
    #     tax_ids = {}
    #     print('master tax')
    #     print('-------------------------------------')
    #     for invoice in self.invoice_ids:
    #         for tax in invoice.tax_line_ids:
    #             print(tax.tax_id.name + ' : ' + str(tax.amount_total))
    #             if tax.tax_id in tax_ids:
    #                 tax_ids[tax.tax_id] = tax_ids[tax.tax_id] + tax.amount_total
    #             else:
    #                 tax_ids[tax.tax_id] = tax.amount_total
    #     print('Compute Tax')
    #     print('-------------------------------------')
    #     # pprint(tax_ids)
    #     for tax in tax_ids:
    #         print (tax.name + ' : ' + str(tax_ids[tax]))

    @api.multi
    def action_submit(self):
        self.ensure_one()
        # print('submit wizard')
        # return self.env.ref('bt_ketronics_od12.action_report_statement_of_account').report_action(self)

        self.name = "Statement of Account"

        # get all invoices
        self.invoice_ids = self.env['account.invoice'].search(['&', '&', '&', ('partner_id', '=', self.partner_id.id), ('type', '=', 'out_invoice'), (
            'date_invoice', '<=', self.end_of_date), ('state', 'in', ['open', 'in_payment', 'paid'])])

        print('Total Untaxed : ')
        for inv in self.invoice_ids:
            self.total_untaxed += inv.amount_untaxed
            self.total_tax += inv.amount_tax
            self.total_with_tax += inv.amount_total
            for line in inv.invoice_line_ids:
                self.total_quantity += line.quantity

        # print('Total Tax : ')
        # print(str(sum(self.invoice_ids.amount_tax)))

        # compute tax
        # self.compute_tax()

        return {
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'statement.of.account',
            'target': 'current',
            'res_id': self.id,
            # 'domain' : [('wizard_stock_on_hand_id','=',self.id)],
            # 'context' : {'search_default_group_location_id':1,'search_default_group_product_id':1},
            # 'context' : ctx,
            'type': 'ir.actions.act_window'
        }

    def generate_excel(self):
        file_name = 'temp'
        workbook = xlsxwriter.Workbook(file_name, {'in_memory': True})
        worksheet = workbook.add_worksheet('Statement of Account')
        worksheet.set_paper(9)  # set A4

        # # Some data we want to write to the worksheet.
        # expenses = (
        #     ['Rent', 1000],
        #     ['Gas',   100],
        #     ['Food',  300],
        #     ['Gym',    50],
        # )

        # # Start from the first cell. Rows and columns are zero indexed.
        # row = 0
        # col = 0

        # # Iterate over the data and write it out row by row.
        # for item, cost in (expenses):
        #     worksheet.write(row, col,     item)
        #     worksheet.write(row, col + 1, cost)
        #     row += 1

        # # Write a total using a formula.
        # worksheet.write(row, 0, 'Total')
        # worksheet.write(row, 1, '=SUM(B1:B4)')

        header_format = workbook.add_format(
            {'bold': True, 'font_size': 16, 'align': 'center'})
        sub_header_format = workbook.add_format(
            {'bold': True, 'font_size': 12, 'align': 'center'})

        content_format = workbook.add_format({'font_size': 10})

        content_center_format = workbook.add_format({'font_size': 10})
        content_center_format.set_align('center')

        content_number_format = workbook.add_format({'font_size': 10})
        content_number_format.set_align('right')
        content_number_format.set_num_format(2)

        content_date_format = workbook.add_format({'font_size': 10})
        content_date_format.set_num_format(15)
        table_content_header_format = workbook.add_format(
            {'bold': True, 'font_size': 10, 'align': 'center'})
        table_content_header_format.set_align('center')
        table_content_header_format.set_align('vcenter')
        table_content_header_format.set_top(1)
        table_content_header_format.set_right(1)
        table_content_header_format.set_bottom(1)
        table_content_header_format.set_left(1)
        first_data_row_num = 11

        sub_total_format = workbook.add_format({'font_size': 10})
        sub_total_format.set_top(1)
        sub_total_format.set_bottom(1)
        sub_total_format.set_bold()
        sub_total_format.set_num_format(2)

        total_format = workbook.add_format({'font_size': 10})
        total_format.set_bold()
        total_format.set_num_format(2)

        worksheet.merge_range(
            0, 0, 0, 8, self.env.user.company_id.name, header_format)
        worksheet.merge_range(
            1, 0, 1, 8, 'STATEMENT OF ACCOUNT', sub_header_format)

        # partner content
        street = self.partner_id.street if self.partner_id.street else ''
        street2 = self.partner_id.street2 if self.partner_id.street2 else ''
        city = self.partner_id.city if self.partner_id.city else ''
        state = self.partner_id.state_id.name if self.partner_id.state_id else ''
        zip_name = self.partner_id.zip if self.partner_id.zip else ''

        worksheet.write(3, 0, self.partner_id.name, content_format)
        worksheet.write(4, 0, street, content_format)
        worksheet.write(5, 0, street2, content_format)
        worksheet.write(6, 0, city + ' ' + state +
                        ' ' + zip_name, content_format)

        # doc parameter
        print_date_str = fields.Date.from_string(
            self.print_date).strftime('%Y%m%d%H%M%S')

        worksheet.write(3, 6, 'Date', content_format)
        worksheet.write(3, 7, ':', content_center_format)
        worksheet.write(3, 8, self.print_date, content_date_format)

        worksheet.write(4, 6, 'Currency', content_format)
        worksheet.write(4, 7, ':', content_center_format)
        worksheet.write(
            4, 8, self.env.user.company_id.currency_id.name, content_format)

        # end of period
        worksheet.merge_range(7, 0, 7, 2, 'Statement of the period ending :  ' +
                              str(self.end_of_date), content_format)

        # table data header
        worksheet.merge_range(9, 0, 10, 0, 'Date', table_content_header_format)
        worksheet.merge_range(9, 1, 10, 1, 'No. Invoice',
                              table_content_header_format)
        worksheet.merge_range(9, 2, 10, 2, 'No. Reff',
                              table_content_header_format)
        worksheet.merge_range(9, 3, 10, 3, 'Model',
                              table_content_header_format)
        worksheet.merge_range(9, 4, 10, 4, 'M/Order',
                              table_content_header_format)
        worksheet.write(9, 5, 'Quantity', table_content_header_format)
        worksheet.write(10, 5, '(Pcs)', table_content_header_format)
        worksheet.merge_range(9, 6, 10, 6, 'Price',
                              table_content_header_format)

        worksheet.merge_range(9, 7, 9, 8, 'Amount',
                              table_content_header_format)
        worksheet.write(10, 7, 'DPP', table_content_header_format)
        worksheet.write(10, 8, 'VAT', table_content_header_format)

        row_line = first_data_row_num
        for inv in self.invoice_ids:
            if len(inv.sale_order_ids) > 0:
                for so in inv.sale_order_ids:
                    qty_per_so = 0.0
                    price_per_so = 0.0

                    worksheet.write(row_line, 0, str(
                        inv.date_invoice), content_format)
                    worksheet.write(row_line, 1, inv.number, content_format)
                    worksheet.write(row_line, 2, so.name, content_format)
                    invoice_lines = inv.invoice_line_ids.filtered(
                        lambda x: x.sale_order_id.id == so.id)

                    for line in invoice_lines:
                        worksheet.write(
                            row_line, 3, line.product_id.name, content_format)
                        mo_number = line.manufacture_order_id.name if line.manufacture_order_id else ''
                        worksheet.write(
                            row_line, 4, mo_number, content_format)
                        worksheet.write(row_line, 5, line.quantity,
                                        content_number_format)
                        worksheet.write(row_line, 6, line.price_unit,
                                        content_number_format)
                        worksheet.write(row_line, 7, line.price_subtotal,
                                        content_number_format)
                        tax_desc = ''
                        for tax_id in line.invoice_line_tax_ids:
                            print(tax_id.description)
                            tax_desc = tax_desc.join(tax_id.description + '; ')
                        worksheet.write(row_line, 8, tax_desc,
                                        content_format)

                        qty_per_so += line.quantity
                        price_per_so += line.price_subtotal
                        row_line += 1

                    # row total per SO
                    worksheet.merge_range(
                        row_line, 0, row_line, 4, '', sub_total_format)
                    worksheet.write(row_line, 5, qty_per_so, sub_total_format)
                    worksheet.write(row_line, 6, '', sub_total_format)
                    worksheet.write(row_line, 7, price_per_so,
                                    sub_total_format)
                    worksheet.write(row_line, 8, '', sub_total_format)
                    row_line += 1

            else:
                qty_per_so = 0.0
                price_per_so = 0.0
                # for invoice create auto
                worksheet.write(row_line, 0, str(
                    inv.date_invoice), content_format)
                worksheet.write(row_line, 1, inv.number, content_format)
                worksheet.write(row_line, 2, inv.origin, content_format)

                for line in inv.invoice_line_ids:
                    worksheet.write(
                        row_line, 3, line.product_id.name, content_format)
                    mo_number = line.manufacture_order_id.name if line.manufacture_order_id else ''
                    worksheet.write(
                        row_line, 4, mo_number, content_format)
                    worksheet.write(row_line, 5, line.quantity,
                                    content_number_format)
                    worksheet.write(row_line, 6, line.price_unit,
                                    content_number_format)
                    worksheet.write(row_line, 7, line.price_subtotal,
                                    content_number_format)
                    tax_desc_no_so = ''
                    print('Tax on Invoice with no SO manual selection')
                    for tax_in_line in line.invoice_line_tax_ids:
                        print(tax_in_line.name)
                        tax_desc_no_so = tax_desc_no_so + tax_in_line.description + '; '
                        # print(tax_id.description)
                        # tax_desc_no_so = tax_desc_no_so.join(tax_id.description + '; ')
                    print('-------------------------------------')
                    worksheet.write(row_line, 8, tax_desc_no_so,
                                    content_format)

                    qty_per_so += line.quantity
                    price_per_so += line.price_subtotal
                    row_line += 1

                # row total per SO
                worksheet.merge_range(
                    row_line, 0, row_line, 4, '', sub_total_format)
                worksheet.write(row_line, 5, qty_per_so, sub_total_format)
                worksheet.write(row_line, 6, '', sub_total_format)
                worksheet.write(row_line, 7, price_per_so,
                                sub_total_format)
                worksheet.write(row_line, 8, '', sub_total_format)
                row_line += 1

        # space before total section
        space_format = workbook.add_format()
        # space_format.set_top(1)
        space_format.set_bottom(1)
        worksheet.merge_range(
            row_line, 0, row_line, 8, '', space_format)

        # TOTAL SECTION
        row_line += 1
        worksheet.write(row_line, 3, 'QUANTITY  :', total_format)
        worksheet.write(row_line, 4, self.total_quantity, total_format)

        worksheet.write(row_line, 6, 'DPP', total_format)
        worksheet.write(
            row_line, 7, ': ' + self.env.user.company_id.currency_id.symbol, total_format)
        worksheet.write(row_line, 8, self.total_untaxed, total_format)
        row_line += 1

        # loop for tax
        tax_ids = self.get_tax_ids()
        for tax in tax_ids:
            worksheet.write(row_line, 6, tax.name, total_format)
            worksheet.write(
                row_line, 7, ': ' + self.env.user.company_id.currency_id.symbol, total_format)
            worksheet.write(row_line, 8, tax_ids[tax], total_format)
            row_line += 1

        worksheet.write(row_line, 6, 'TOTAL', total_format)
        worksheet.write(
            row_line, 7, ': ' + self.env.user.company_id.currency_id.symbol, total_format)
        worksheet.write(row_line, 8, self.total_with_tax, total_format)
        row_line += 1

        # space between total and footer
        worksheet.merge_range(
            row_line, 0, row_line, 8, '', space_format)
        row_line += 2

        # FOOTER SECTION
        if self.env.user.company_id.invoice_footer_note:
            footnote_format = workbook.add_format()
            footnote_format.set_font_size('8')
            footnote_format.set_align('left')
            footnote_format.set_align('top')

            worksheet.merge_range(
                row_line, 0, row_line+7, 3, self.env.user.company_id.invoice_footer_note, content_format)

            signature_format = workbook.add_format()
            signature_format.set_align('center')

            worksheet.merge_range(row_line, 5, row_line,
                                  6, 'Issued by,', signature_format)
            worksheet.merge_range(
                row_line+7, 5, row_line+7, 6, '________________________,', signature_format)
            worksheet.merge_range(row_line+8, 5, row_line+8,
                                  6, 'Authorized Signature,', signature_format)

        workbook.close()

        with open(file_name, "rb") as file:
            file_base64 = base64.b64encode(file.read())
        self.carrier_xlsx_document_name = 'StatementOfAccount.xlsx'  # + '.xlsx'
        self.write({'carrier_xlsx_document': file_base64, })
