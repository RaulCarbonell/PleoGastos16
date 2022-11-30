# -*- coding: utf-8 -*-

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    pleo_partner_id = fields.Many2one('res.partner', string='Proveedor genérico')
    account_journal_ticket_id = fields.Many2one('account.journal', string='Diario contable Ticket')
    account_journal_bank_id = fields.Many2one('account.journal', string='Diario contable Banco')
