# -*- coding: utf-8 -*-

import logging

from odoo import api, fields, models
from odoo.exceptions import UserError


_logger = logging.getLogger(__name__)


class WizardProcesarRegistro(models.TransientModel):
    _name = 'wizard.procesar_registros'
    _description = 'Wizard procesar registros Pleo'

    notes = fields.Text('Observaciones', readonly=True,
                        default=lambda self: 'Registros a procesar: {}'.format(len(self.env.context['active_ids'])))

    def process(self):
        # TODO: Analizar un control para advertir que existen registros NO seleccionados del mismo recibo.
        active_ids = self.env.context['active_ids']
        records = self.env['pleo.ticket'].browse(active_ids)
        records.process()
