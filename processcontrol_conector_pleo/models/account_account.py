# -*- coding: utf-8 -*-

from odoo import models, fields
from odoo.exceptions import UserError


class AccountAccount(models.Model):
    _inherit = "account.account"

    is_pocket_account = fields.Boolean('Es cuenta pocket')
