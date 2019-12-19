from odoo import api, fields, models


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sender_by = fields.Char('Sender by')

    # _pick_manufacture_type = fields.Selection([
    #     ('in_house', 'In House'),
    #     ('subcon', 'Subconract'),
    # ], string='Manufacture Type', compute="_compute_manufacture_type"], store=True)

    pick_manufacture_type = fields.Selection([
        ('in_house', 'In House'),
        ('subcon', 'Subconract'),
    ], string='Manufacture Type', )

    proc_compute = fields.Char(
        compute='_compute_procurement', string='Total', store=True)

    @api.depends('move_ids_without_package')
    def _compute_procurement(self):
        print('inside ciompute procurement')
        for rec in self:
            print('inside move')
            for move in rec.move_ids_without_package:
                if move.sale_line_id:

                    self.env.cr.execute('update stock_move set sale_order_id = ' + str(
                        move.sale_line_id.order_id.id) + ' where id = ' + str(move.id))
