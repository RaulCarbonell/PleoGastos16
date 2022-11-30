# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    is_pocket_move = fields.Boolean('Es asiento gasto pocket')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    is_pocket_move = fields.Boolean('Es asiento gasto pocket', related='move_id.is_pocket_move')
