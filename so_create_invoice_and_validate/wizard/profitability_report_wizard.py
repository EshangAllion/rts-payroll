from odoo import models, fields, api
from datetime import datetime, date, time, timedelta
from odoo.exceptions import ValidationError
import xlsxwriter
import base64
from odoo.tools import misc
import math
import os
import calendar


class ProfitabilityReportWizard(models.TransientModel):
    _name = 'profitability.report.wizard'

    start_date = fields.Date("From")
    end_date = fields.Date("To")

    report_file = fields.Binary('File', readonly=True)
    report_name = fields.Text(string='File Name')
    is_printed = fields.Boolean('Printed', default=False)

    @api.multi
    def get_report(self):
        """ths function will check the start date, end date of the requested report and make the report file"""
        if self.start_date and self.end_date:
            self.profitability_report()
            filename = 'Profitability Report' + '.xlsx'
            my_report_data = open(filename, 'rb+')  # converting the report to binary
            f = my_report_data.read()
            output = base64.encodestring(f)
            cr, uid, context = self.env.args
            ctx = dict(context)
            ctx.update({'report_file': output})
            ctx.update({'file': filename})
            self.env.args = cr, uid, misc.frozendict(context)
            self.report_name = filename  # Add values for field
            self.report_file = ctx['report_file']
            self.is_printed = True

            # create a dictionary and pass it to the view
            result = {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'profitability.report.wizard',
                'target': 'new',
                'context': ctx,
                'res_id': self.id,
            }
            os.remove(filename)
            # return the dictionary
            return result
        else:
            raise ValidationError("Please Select The Report Date")

    @api.multi
    def profitability_report(self):
        """This function creates the content according to the report type (Profitability Report.xlsx) """

        # create file name
        filename = 'Profitability Report' + '.xlsx'
        # create the workbook and worksheet
        workbook = xlsxwriter.Workbook(filename)
        worksheet = workbook.add_worksheet()
        worksheet.set_landscape()

        # Layouts and styles of the report
        border = workbook.add_format({'border': 1})
        bold = workbook.add_format({'bold': True, 'border': 1, 'align': 'center'})
        font_left = workbook.add_format({'align': 'left', 'border': 1, 'font_size': 12})
        numeric_round = workbook.add_format({'align': 'left', 'border': 1, 'font_size': 12, 'num_format': '#,###.##'})

        font_center = workbook.add_format({'align': 'center', 'border': 1, 'valign': 'vcenter', 'font_size': 12})
        font_bold_center = workbook.add_format(
            {'align': 'center', 'border': 1, 'valign': 'vcenter', 'font_size': 12,
             'bold': True})
        total = workbook.add_format(
            {'bold': True, 'align': 'left', 'border': 1, 'font_size': 12, 'num_format': '#,###.##'})

        # report border
        worksheet.set_column('F:XFD', None, None, {'hidden': True})
        worksheet.set_column('A:E', 20, border)
        worksheet.set_row(0, 20)
        # heading of the report
        worksheet.merge_range('A1:G1', 'PARAMOUNT DISTRIBUTOR', bold)
        worksheet.merge_range('A2:G2', 'INVOICE PROFITABILITY REPORT -' + str(self.start_date) + ' to ' + str(
            self.end_date), bold)

        # define the rows and columns of the report
        row = 2
        col = 0

        # columns heading
        worksheet.merge_range(row, col, row + 1, col, "Invoice", font_bold_center)
        worksheet.merge_range(row, col + 1, row + 1, col + 1, "Total Cost Price", font_bold_center)
        worksheet.merge_range(row, col + 2, row + 1, col + 2, "Total Selling price", font_bold_center)
        worksheet.merge_range(row, col + 3, row + 1, col + 3, "Profit Amount", font_bold_center)
        worksheet.merge_range(row, col + 4, row + 1, col + 4, "Profitability (%)", font_bold_center)

        row += 2

        invoices_obj = self.env['account.invoice']
        total_cost = 0
        total_selling_price = 0

        for invoice in invoices_obj.search([('state', '!=', 'draft'),
                                            ('date_invoice', '>=', self.start_date),
                                            ('date_invoice', '<=', self.end_date),
                                            ('type', '=', 'out_invoice')]):

            # first_record = self.env['account.invoice.line'].search([('invoice_id', '=', invoice.id)])[0]
            if invoice:
                worksheet.write(row, col, invoice.number, font_left)  # Customer Tin

                for invoice_line in invoice.invoice_line_ids:

                    total_cost += invoice_line.quantity * invoice_line.product_id.standard_price  # calculate the total cost
                    total_selling_price += invoice_line.quantity * invoice_line.price_unit  # calculate the total selling price

                    worksheet.write(row+1, col, invoice.number, font_left)  # requested invoices
                    worksheet.write(row, col + 1, total_cost, font_left)  # Total Cost Price
                    worksheet.write(row, col + 2, invoice_line.quantity * invoice_line.price_unit, font_left)  # Total Selling price
                    worksheet.write(row, col + 3, float(total_selling_price - total_cost), font_left)  # Profit Amount
                    worksheet.write(row, col + 4, float((total_selling_price - total_cost) / total_selling_price * 100), numeric_round)  # Profitability

                row += 1

        # close the work book
        workbook.close()
        return filename