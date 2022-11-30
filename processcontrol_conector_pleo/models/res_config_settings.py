# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pleo_partner_id = fields.Many2one('res.partner', related="company_id.pleo_partner_id", readonly=False,
                                      string='Proveedor genérico')
    account_journal_ticket_id = fields.Many2one('account.journal', related="company_id.account_journal_ticket_id",
                                                readonly=False, string='Diario contable Tiquet')
    account_journal_bank_id = fields.Many2one('account.journal', related="company_id.account_journal_bank_id",
                                              readonly=False, string='Diario contable Banco')