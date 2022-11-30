# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class Ticket(models.Model):
    _name = 'pleo.ticket'
    _description = 'Ticket de Pleo'
    _rec_name = 'receipt'
    _inherit = 'mail.thread'

    receipt = fields.Char(string='Número de Recibo',
                          help='Secuencia Pleo: Identificador para cada uno de los tickets/Facturas de compras hechas '
                               'con Pleo.',
                          required=True, tracking=True, states={'realizado': [('readonly', True)]})
    # receipt_type = fields.Selection([('factura', 'ticket (Factura de Proveedor)'),
    #                                  ('ticket', 'ticket'),
    #                                  ('factura_multi_iva', 'ticket (Factura de Proveedor) con más de un IVA'),
    #                                  ('gasto_pocket', 'Gastos Pocket (En Efectivo)'),
    #                                  ('reembolso_pocket', 'Reembolso Pocket'),
    #                                  ('desconocido', 'Desconocido')
    #                                  ], string='Tipo de recibo', required=True,
    #                                 compute='_compute_receipt_type', store=True)
    date = fields.Datetime(string='Fecha de Liquidación',
                           help='Fecha en la que el pago fue liquidado.', required=True, tracking=True,
                           states={'realizado': [('readonly', True)]})
    text = fields.Text(string='Descripción',
                       help='Descripción del gasto: puede ser una combinación de parámetros (ej: comercio+empleado)',
                       required=True, tracking=True, states={'realizado': [('readonly', True)]})
    amount = fields.Monetary(string='Importe Liquidado', help='Cantidad liquidada en Euros.', required=True,
                             tracking=True, states={'realizado': [('readonly', True)]})
    tax_code = fields.Char(string='Codigo Fiscal',
                           help='Normalmente es un codigo que sage asigna (ej: S01) o una cuenta contable para IVA '
                                '(ej: 47200001)',
                           tracking=True, states={'realizado': [('readonly', True)]})
    tax_percentage = fields.Float(string='Porcentaje de Impuesto',
                                  help='Es el valor del impuesto en porcentaje (ej: 21%)',
                                  tracking=True, states={'realizado': [('readonly', True)]})
    tax_amount = fields.Monetary(string='Importe del Impuesto',
                                 help='Cálculo del impuesto de acuerdo a la base imponible multiplicado por el '
                                      'porcentaje del impuesto.',
                                 tracking=True, states={'realizado': [('readonly', True)]})
    contra_account = fields.Char(string='Cuenta de Contrapartida',
                                 help='Normalmente, Pleo es creada en el sistema de contabilidad como un Banco. '
                                      'El número asociado a esta cuenta será el número de contrapartida.',
                                 required=True, tracking=True, states={'realizado': [('readonly', True)]})
    cif = fields.Char(string='CIF',
                      help='Cif del establecimiento de comercio. Este es un campo que hoy en día es ingresado '
                           'manualmente por el Admin (No siempre estará populada la celda)',
                      tracking=True, states={'realizado': [('readonly', True)]})
    document_number = fields.Char(string='Número de Documento/Factura',
                                  help='Número que está impreso en el ticket o factura que el usuario recibe. '
                                       'Este es un campo que hoy en día es ingresado manualmente por el Admin '
                                       '(No siempre estará populada la celda)',
                                  tracking=True, states={'realizado': [('readonly', True)]})
    category = fields.Char(string='Nombre de la Categoría', help='Nombre del tipo de Gasto (ej: Dietas)',
                           tracking=True, states={'realizado': [('readonly', True)]})
    account_number = fields.Char(string='Número de Cuenta',
                                 help='Número de la cuenta contable asociada a la categoría (ej: Dietas)',
                                 tracking=True, states={'realizado': [('readonly', True)]})
    owner = fields.Char(string='Nombre del Empleado', help='Nombre del usuario que realiza la compra.',
                        required=True, tracking=True, states={'realizado': [('readonly', True)]})
    employee_code = fields.Char(string='Código del Empleado', help='Código o Centro de Costo asociado al usuario.',
                                tracking=True, states={'realizado': [('readonly', True)]})
    note = fields.Text(string='Nota', help='Campo libre designado al usuario para dejar una nota.', tracking=True,
                       states={'realizado': [('readonly', True)]})
    department = fields.Char(string='Nombre del Equipo',
                             help='Nombre del equipo/departamento al cual pertenece el usuario.',
                             tracking=True, states={'realizado': [('readonly', True)]})
    department_code = fields.Char(string='Codigo del Equipo',
                                  help='Codigo o Centro de Costo asociado al equipo/departamento.',
                                  tracking=True, states={'realizado': [('readonly', True)]})
    receipt_url = fields.Char(string='URL del Ticket', help='URL del Ticket', tracking=True,
                              states={'realizado': [('readonly', True)]})
    cliente_tag = fields.Char(string='Cliente - Tag')
    proyecto_tag = fields.Char(string='Proyecto - Tag')
    state = fields.Selection(string='Estado', selection=[('pendiente', 'Pendiente'),
                                                         ('error', 'Error'),
                                                         ('realizado', 'Realizado')],
                             default='pendiente', required=True, tracking=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Compañía', required=True, readonly=True,
                                 default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id')

    def _get_receipt_type(self):
        """
        Determina el tipo de recibo
        Returns: tipo de recibo (string), signo (int)

        """
        # Tipo de recibo.
        if self.cif:
            receipt_type = 'factura'
        elif self._is_bills_pocket() and self.amount < 0.0:
            receipt_type = 'gasto_pocket'
        elif self._is_bills_pocket() and self.amount > 0.0:
            receipt_type = 'reembolso_pocket'
        elif not self.cif:
            receipt_type = 'ticket'
        else:
            receipt_type = ''

        # Signo
        if self.amount >= 0.0:
            sign = 1
        else:
            sign = -1

        return receipt_type, sign

    def _get_analytic_tag_by_name(self, name):
        """
        Busca la etiqueta analítica por name en la Empresa del registro.
        Args:
            name: Nombre de la etiqueta

        Returns: instancias account.analytic.tag

        """
        return self.env['account.analytic.tag'].search(['|',
                                                        ('company_id', '=', False),
                                                        ('company_id', '=', self.company_id.id),
                                                        ('name', '=', name)])

    def _get_account_by_code(self, code):
        """
        Busca la cuenta contable por código en la Empresa del registro.
        Args:
            code: Código de cuenta contable

        Returns: instancias account.account

        """
        return self.env['account.account'].search([('code', '=', code),
                                                   ('company_id', '=', self.company_id.id)])

    def _get_purchase_tax_by_percentage_account(self):
        """
        Busca los impuestos del tipo Compras (purchase) que coincidan con el porcentaje y al menos tenga la cuenta.
        Returns: primera instancia account.tax

        """
        tax_percentage = self.tax_percentage * 100
        taxes = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'),
                                                ('amount', '=', tax_percentage),
                                                ('company_id', '=', self.company_id.id)])
        for tax in taxes:
            for line in tax.invoice_repartition_line_ids:
                if line.account_id and line.account_id.code == self.tax_code:
                    return tax
        return None

    def _get_partner_by_cif(self):
        """
        Busca los Partners por CIF
        Returns: instancias res.partner

        """
        if self.cif:
            return self.env['res.partner'].search([('vat', '=', self.cif)])
        return None

    def _get_receipts(self):
        """
        Agrupa los registros por receipt y los clasifica por tipo de documento a generar.
        Establece los ids de los modelos relacionados, por ejemplo, para un número de cuenta, asigna el id de la cuenta.
        Returns: dict

        """
        receipts = {}
        for record in self:
            # Armo los diccionarios con la estructura de datos.
            # Recupero el tipo de recibo.
            receipt_type, sign = record._get_receipt_type()
            # Cabecera
            # Recupero los ids de las instancias.
            # partner_id
            partner_id = record._get_partner_by_cif()
            # account_number
            account_number = record._get_account_by_code(record.account_number)
            # contra_account
            contra_account = self._get_account_by_code(record.contra_account)
            # cliente_tag
            cliente_tag = record._get_analytic_tag_by_name(record.cliente_tag)
            # proyecto_tag
            proyecto_tag = record._get_analytic_tag_by_name(record.proyecto_tag)

            account_analytic_tag_ids = []
            if cliente_tag:
                account_analytic_tag_ids.append(cliente_tag.id)
            if proyecto_tag:
                account_analytic_tag_ids.append(proyecto_tag.id)

            header = {
                'receipt': record.receipt,  # Es redundante el dato, pero lo necesito.
                'date': record.date,
                'text': record.text or '',
                'partner_id': partner_id.id if partner_id else None,
                'document_number': record.document_number or '',
                'owner': record.owner or '',
                'employee_code': record.employee_code or '',
                'category': record.category or '',
                'account_number': account_number.id,
                'contra_account': contra_account.id,
                'note': record.note or '',
                'department': record.department or '',
                'department_code': record.department_code or '',
                'receipt_url': record.receipt_url or '',
                'orig_amount': record.amount * sign,  # TODO: Para qué sirve?
                'currency_id': record.currency_id.id,
                'company_id': record.company_id.id,
                'account_analytic_tag_ids': account_analytic_tag_ids,
            }

            # Detalle
            # Instancias
            # tax_id: Tomo el primero de la lista.
            tax = record._get_purchase_tax_by_percentage_account()
            # Calculos
            # amount: el amount suma el impuesto, por lo que hay que restarlo.
            amount = (record.amount * sign) - (record.tax_amount * sign)

            detail = {
                'amount': amount,
                'tax_id': tax.id if tax else None,
                # 'tax_amount': record.tax_amount
            }

            if record.receipt in receipts:
                if receipts[record.receipt]['tipo'] == receipt_type:
                    receipts[record.receipt]['detail'].append(detail)
                    receipts[record.receipt]['header']['orig_amount'] += detail['amount']
                else:
                    raise ValidationError('El recibo {} tiene una inconsistencia al momento de clasificar '
                                          'uno de sus IVA.'.format(record.receipt))
            else:
                receipts[record.receipt] = {
                    'tipo': receipt_type,
                    'header': header,
                    'detail': [detail]
                }
        return receipts

    def _get_journal_by_account_id(self, account_id):
        """
        Recupera un journal a partir de su cuenta contable.
        Returns: instancias account.journal

        """
        # TODO: Verificar esta búsqueda. ¿Si encuentro mas de un journal, cuál tomo?
        # TODO: Control de existencia de journal.
        journal = self.env['account.journal'].search([('type', '=', 'bank'),
                                                      ('default_account_id', '=', account_id),
                                                      ('company_id', '=', self.company_id.id)])
        return journal[0] if journal else None

    def _get_partner_employee_by_code(self, code):
        """
        Recupera el partner asociado (dirección privada) al empleado
        a partir del codigo del empleado (identification_id)
        Returns: instancia res.partner

        """
        employee = self.env['hr.employee'].search([('identification_id', '=', code)])
        if employee and len(employee) == 1 and employee.address_home_id:
            return employee.address_home_id
        else:
            return None

    def _is_bills_pocket(self):
        """
        Reembolso Pocket: Utiliza el campo account_number para determinar si es un reembolso pocket.
        Returns: boolean

        """
        contra_account = self._get_account_by_code(self.contra_account)
        return True if contra_account and contra_account.is_pocket_account else False

    def _prepare_invoice_values(self, data):
        header = data['header']
        details = data['detail']

        # Armo el detalle.
        invoice_line_ids = []
        sequence = 10
        for detail in details:
            invoice_line = {
                'name': header['text'],
                'sequence': sequence,
                'quantity': 1.0,
                'price_unit': detail['amount'],
                'account_id': header['account_number'],
                'display_type': False,
                'analytic_account_id': False,
                'analytic_tag_ids': [(6, 0, header['account_analytic_tag_ids'])],
            }
            if detail['tax_id']:
                invoice_line['tax_ids'] = [(6, 0, [detail['tax_id']])]
            invoice_line_ids.append((0, 0, invoice_line))
            sequence += 1

        # Armo la cabecera.
        ref = header['receipt']
        move_type = 'in_invoice'  # Factura de proveedor.
        narration = header['receipt_url']
        currency_id = header['currency_id']
        invoice_date = header['date'].date()
        partner = self.env['res.partner'].browse(header['partner_id'])
        partner_invoice_id = partner.address_get(['invoice'])['invoice']
        partner_bank_id = partner.commercial_partner_id.bank_ids.filtered_domain(['|', ('company_id', '=', False), ('company_id', '=', self.company_id.id)])[:1]
        fiscal_position = self.env['account.fiscal.position'].get_fiscal_position(partner_invoice_id)
        payment_reference = header['note']
        company_id = header['company_id']

        # Recupero el journal.
        journal = self.env['account.move'].with_context(default_move_type=move_type)._get_default_journal()
        if not journal:
            raise UserError(_('Please define an accounting purchase journal for the company %s (%s).') % (self.company_id.name, self.company_id.id))

        invoice_vals = {
            'ref': ref,
            'move_type': move_type,
            'narration': narration,
            'currency_id': currency_id,
            'invoice_date': invoice_date,
            # 'invoice_user_id': self.user_id and self.user_id.id or self.env.user.id, TODO: es el empleado?
            'partner_id': partner_invoice_id,
            'fiscal_position_id': fiscal_position,
            'payment_reference': payment_reference,
            'partner_bank_id': partner_bank_id.id,
            # 'invoice_origin': self.name,
            # 'invoice_payment_term_id': self.payment_term_id.id,
            'invoice_line_ids': invoice_line_ids,
            'company_id': company_id,
        }
        return invoice_vals

    def _create_payments(self, data):
        """
        Crea el wizard de pago, lo procesa y reconcilia.
        Returns: instancia

        """
        journal_id = self._get_journal_by_account_id(data['header']['contra_account'])
        payment_date = data['header']['date']

        payment_wizard = self.env['account.payment.register'].create({
            'journal_id': journal_id.id,
            'payment_date': payment_date,
        })
        payment = payment_wizard._create_payments()

        return payment

    def _reconciliation(self, bank_statement, payment):
        """
        Concilia el extracto bancario y el pago.
        Args:
            bank_statement:
            payment:

        Returns:

        """
        st_line_ids = bank_statement.line_ids.ids
        line_ids = payment.move_id.line_ids.filtered(lambda l: l.credit > 0)
        lines_vals_list = []
        for line in line_ids:
            if (line.name or '/') == '/':
                line_name = line.move_id.name
            else:
                line_name = line.name
            lines_vals_list.append({
                'name': '%s: %s' % (line.move_id.name, line_name),
                'balance': -line.amount_currency if line.currency_id else -line.balance,
                'analytic_tag_ids': [[6, None, []]],
                'id': line.id,
                'currency_id': line.currency_id.id
            })

        data = [{
            'partner_id': payment.partner_id.id,
            'lines_vals_list': lines_vals_list,
            'to_check': False
        }]

        self.env['account.reconciliation.widget'].process_bank_statement_line(st_line_ids, data)

    def _create_bank_statement(self, data, amount):
        """
        Genera un extracto bancario por cada factura.
        Args:
            data:

        Returns: instancia account.bank.statement

        """
        name = data['header']['receipt']
        journal_id = self._get_journal_by_account_id(data['header']['contra_account'])
        date = data['header']['date']
        partner_id = data['header']['partner_id']

        statement_id = self.env['account.bank.statement'].create({
            'name': name,
            'journal_id': journal_id.id,
            'date': date,
            'line_ids': [[0, 0, {
                'date': date,
                'payment_ref': name,
                'partner_id': partner_id,
                'amount': amount}]]
        })
        statement_id.button_post()

        return statement_id

    def general_controls(self):
        """
        Controles generales.
        Returns:

        """
        # Verifica configuración cuenta analítica.
        group_analytic_tags_id = self.env.ref('analytic.group_analytic_tags').id
        user_group_analytic_tags = self.env.user.groups_id.filtered(lambda g: g.id == group_analytic_tags_id)
        if not user_group_analytic_tags:
            raise UserError('Debe habilitar la opción Etiquetas Analíticas desde la configuración de la Contabilidad.')

        # Todos los registros deben estar en un estado distinto a realizado.
        records = self.filtered(lambda r: r.state == 'realizado')
        if records:
            raise UserError('No puede incluir los siguientes registros porque ya se encuentran procesados.'
                            '\nReceipts: {}'.format(', '.join([r.receipt for r in records])))
        # Busco los taxes de compra. # TODO: Ver el ticket sin impuestos, no es necesario este control como general.
        taxes = self.env['account.tax'].search([('type_tax_use', '=', 'purchase'),
                                                ('company_id', '=', self.env.company.id)])
        if not taxes:
            raise UserError('Debe parametrizar al menos un impuesto de compra en el Sistema.')

    def controls(self):
        """
        Controles para procesar registros de Pleo. Registra notificaciones y cambios de estado en cada registro.
        Returns:
        """
        # Controles generales.
        self.general_controls()

        # Controles por registro.
        errors = ''
        for record in self:
            error = ''
            # date
            if record.date > fields.Datetime.now():
                error += '\n  La Fecha no puede ser futura.'

            # amount: Tener en cuenta los valores positivos en el caso de Reembolso pocket.
            if record.amount == 0.0:
                error += '\n  El Importe Liquidado no puede ser cero.'
            if not record._is_bills_pocket() and record.amount > 0.0:
                error += '\n  El Importe Liquidado debe ser menor a cero.'

            # tax_percentage
            if record.tax_percentage < 0.0:
                error += '\n  El Porcentaje de Impuesto debe ser mayor a cero.'

            # tax_code: El código del impuesto debe existir en la base como cuenta contable.
            if record.tax_percentage > 0.0:
                tax_code = self._get_account_by_code(record.tax_code)
                if tax_code:
                    if not record._get_purchase_tax_by_percentage_account():
                        error += '\n  No se encontró un impuesto de compra para el Porcentaje de ' \
                                 'Impuesto {} y Codigo Fiscal {}.'.format(record.tax_percentage,
                                                                          record.tax_code)
                else:
                    error += '\n  La cuenta de Codigo Fiscal {} no se encontró en el plan de cuentas, ' \
                             'por favor, verifique.'.format(record.tax_code)

                    # tax_amount: Tener en cuenta los valores positivos en el caso de Reembolso pocket.
                    if record.tax_amount == 0.0:
                        error += '\n  El Importe del Impuesto no puede ser cero.'
                    if not record._is_bills_pocket() and record.tax_amount > 0.0:
                            error += '\n  El Importe del Impuesto debe ser menor a cero.'

            # contra_account: Verificar que la cuenta exista en el plan de cuentas y debe existir un diario.
            contra_account = self._get_account_by_code(record.contra_account)
            if not contra_account:
                error += '\n  La Cuenta de Contrapartida {} no se encontró en el plan de cuentas, ' \
                         'por favor, verifique.'.format(record.contra_account)
            else:
                account_journal = self._get_journal_by_account_id(record.contra_account)
                if not account_journal:
                    error += '\n  No existe un diario contable para la cuenta de contrapartida {}, ' \
                             'por favor, verifique.'.format(record.contra_account)

            # cif: Si viene cif, debe existir en el Sistema y debe ser único.
            if record.cif:
                partners = record._get_partner_by_cif()
                if not partners:
                    error += '\n  No se encontró un Partner con el CIF {}'.format(record.cif)
                elif len(partners) > 1:
                    error += '\n  Se encontró mas de un Partner con el CIF {}'.format(record.cif)

            # account_number
            if record.account_number:
                account_number = self._get_account_by_code(record.account_number)
                if not account_number:
                    error += '\n  El Número de Cuenta {} no se encontró en el plan de cuentas, ' \
                             'por favor, verifique.'.format(record.account_number)

            # cliente_tag
            if record.cliente_tag:
                cliente_tag = self._get_analytic_tag_by_name(record.cliente_tag)
                if not cliente_tag:
                    error += '\n  No se encontró la etiqueta analítica {}, ' \
                             'por favor, verifique.'.format(record.cliente_tag)

            # proyecto_tag
            if record.proyecto_tag:
                proyecto_tag = self._get_analytic_tag_by_name(record.proyecto_tag)
                if not proyecto_tag:
                    error += '\n  No se encontró la etiqueta analítica {}, ' \
                             'por favor, verifique.'.format(record.proyecto_tag)

            if error:
                # Agrego una notificación.
                record.message_post(body='<strong>Errores al procesar el registro:</strong>'
                                         '{}'.format(error.replace('\n', '<br/>')))
                # Cambio el estado del registro.
                record.state = 'error'
                # Agrego el error del registro al mensaje general para mostrar en pantalla.
                errors += '\nRecibo {}:{}\n'.format(record.receipt, error)

        if errors:
            # Realizo commit para devolver el error al usuario y actualizar los estados y mensajes.
            self.env.cr.commit()
            raise ValidationError('Se encontraron los siguientes errores al intentar procesar los registros:' +
                                  errors)

    def create_invoice(self, data):
        """
        Genera la factura correspondiente.
        Returns:

        """
        # Preparo los datos para generar las facturas.
        invoice_vals = self._prepare_invoice_values(data)
        # Genero la factura. TODO: Evaluar la compañía para crear.
        move = self.env['account.move']
        AccountMove = self.env['account.move'].with_context(default_move_type='in_invoice')
        move |= AccountMove.with_company(self.env.company).create(invoice_vals)
        # Valido la factura.
        move.action_post()
        # Creo el pago.
        payment = self.with_context(active_model='account.move', active_ids= move.ids)._create_payments(data)
        # Creo el extracto bancario.
        bank_statement = self._create_bank_statement(data, payment.amount)
        # Concilio el extracto y el pago.
        self._reconciliation(bank_statement, payment)
        # Valido el extracto bancario.
        bank_statement.button_validate()

    def create_ticket(self, data):
        """
        Gastos sin CIF.
        Args:
            data:

        Returns:

        """
        # Ticket.
        # Recupero el diario contable de operaciones varias de la configuración.
        journal_id = self.env.company.account_journal_ticket_id
        if not journal_id:
            raise UserError('Debe indicar un diario contable del tipo Operaciones varias en la configuración del '
                            'módulo para la generación de tickets sin CIF.')
        # Recupero el diario contable de la cuenta de contrapartida.
        journal_bank_id = self._get_journal_by_account_id(data['header'].get('contra_account'))

        # Recupero el partner asociado al empleado o el proveedor genérico.
        partner = None
        # Partner del empleado.
        employee_code = data['header'].get('employee_code')
        if employee_code:
            partner = self._get_partner_employee_by_code(employee_code)
        # Proveedor genérico.
        if not partner:
            partner = self.env.company.pleo_partner_id
        if not partner:
            raise UserError('Debe indicar un proveedor genérico en la configuración del módulo para la '
                            'generación de tickets sin CIF.')

        # Líneas del asiento.
        lines = []
        # Haber
        line = {
            'account_id': partner.property_account_payable_id.id or None,
            'partner_id': partner.id,
            'credit': data['header']['orig_amount']
        }
        lines.append([0, 0, line])
        # Debe
        for l in data['detail']:
            # Importe
            line = {
                'account_id': data['header']['account_number'],
                'partner_id': partner.id,
                'debit': l['amount'],
                'analytic_tag_ids': [(6, 0, data['header']['account_analytic_tag_ids'])],
            }
            lines.append([0, 0, line])
            if l['tax_id']:
                tax_id = l['tax_id']
                res = self.env['account.tax'].browse(tax_id).compute_all(l['amount'])
                if res and res.taxes:
                    for t in res.taxes:
                        # Impuesto
                        line = {
                            'account_id': t['account_id'] or None,
                            'partner_id': partner.id,
                            'debit': t['amount']
                        }
                        lines.append([0, 0, line])
        # Cabecera del asiento.
        vals = {
            'ref': data['header']['text'],
            'date': data['header']['date'],
            'journal_id': journal_id.id,
            'line_ids': lines
        }
        # Creo el asiento.
        account_move = self.env['account.move'].create(vals)
        account_move.action_post()

        # Asiento del banco.
        # Líneas del asiento.
        lines = []
        # Haber
        line = {
            'account_id': journal_bank_id.default_account_id.id,
            'partner_id': partner.id,
            'credit': data['header']['orig_amount']
        }
        lines.append([0, 0, line])
        # Debe
        line = {
            'account_id': partner.property_account_payable_id.id or None,
            'partner_id': partner.id,
            'debit': data['header']['orig_amount']
        }
        lines.append([0, 0, line])
        # Cabecera del asiento.
        vals = {
            'ref': data['header']['text'],
            'date': data['header']['date'],
            'journal_id': journal_bank_id.id,
            'partner_id': partner.id,
            'line_ids': lines
        }
        # Creo el asiento.
        account_move_bank = self.env['account.move'].create(vals)
        account_move_bank.action_post()

        # Concilio.
        account_move_lines = account_move.line_ids.\
            filtered(lambda l: l.reconciled == False and l.account_id == partner.property_account_payable_id)
        account_move_bank_lines = account_move_bank.line_ids.\
            filtered(lambda l: l.reconciled == False and l.account_id == partner.property_account_payable_id)
        (account_move_lines + account_move_bank_lines).reconcile()

    def create_gasto_pocket(self, data):
        """
        Gasto pocket.
        Args:
            data:

        Returns:

        """
        # Gasto pocket.
        # Recupero el diario contable de operaciones varias de la configuración.
        journal_id = self.env.company.account_journal_ticket_id
        if not journal_id:
            raise UserError('Debe indicar un diario contable del tipo Operaciones varias en la configuración del '
                            'módulo para la generación del gasto pocket.')
        # Recupero el diario contable de bancos de la configuración.
        # journal_bank_id = self.env.company.account_journal_bank_id
        # if not journal_bank_id:
        #     raise UserError('Debe indicar un diario contable del tipo Banco en la configuración del módulo para la '
        #                     'generación del gasto pocket.')

        # Recupero el partner asociado al empleado o el proveedor genérico.
        partner = None
        # Partner del empleado.
        employee_code = data['header'].get('employee_code')
        if employee_code:
            partner = self._get_partner_employee_by_code(employee_code)
        # Proveedor genérico.
        if not partner:
            partner = self.env.company.pleo_partner_id

        if not partner:
            raise UserError('Debe indicar un proveedor genérico en la configuración del módulo para la '
                            'generación del gasto pocket.')

        # Líneas del asiento.
        lines = []
        # Haber
        line = {
            'account_id': partner.property_account_payable_id.id or None,
            'partner_id': partner.id,
            'credit': data['header']['orig_amount']
        }
        lines.append([0, 0, line])
        # Debe
        for l in data['detail']:
            # Importe
            line = {
                'account_id': data['header']['account_number'],
                'partner_id': partner.id,
                'debit': l['amount'],
                'analytic_tag_ids': [(6, 0, data['header']['account_analytic_tag_ids'])],
            }
            lines.append([0, 0, line])
            if l['tax_id']:
                tax_id = l['tax_id']
                res = self.env['account.tax'].browse(tax_id).compute_all(l['amount'])
                if res and res.taxes:
                    for t in res.taxes:
                        # Impuesto
                        line = {
                            'account_id': t['account_id'] or None,
                            'partner_id': partner.id,
                            'debit': t['amount']
                        }
                        lines.append([0, 0, line])
        # Cabecera del asiento.
        vals = {
            'ref': data['header']['text'],
            'date': data['header']['date'],
            'journal_id': journal_id.id,
            'partner_id': partner.id,
            'line_ids': lines,
            'is_pocket_move': True,
        }
        # Creo el asiento.
        account_move = self.env['account.move'].create(vals)
        account_move.action_post()

    def create_reembolso_pocket(self, data):
        """

        Args:
            data:

        Returns:

        """
        # Reembolso pocket.
        # Recupero el diario contable de operaciones varias de la configuración.
        journal_id = self.env.company.account_journal_ticket_id
        if not journal_id:
            raise UserError('Debe indicar un diario contable del tipo Operaciones varias en la configuración del '
                            'módulo para la generación del reembolso pocket.')
        # Recupero el diario contable de bancos de la configuración.
        # journal_bank_id = self.env.company.account_journal_bank_id
        # if not journal_bank_id:
        #     raise UserError('Debe indicar un diario contable del tipo Banco en la configuración del módulo para la '
        #                     'generación del reembolso pocket.')
        # Recupero el diario contable de la cuenta de contrapartida.
        journal_bank_id = self._get_journal_by_account_id(data['header'].get('contra_account'))

        # Recupero el partner asociado al empleado o el proveedor genérico.
        partner = None
        # Partner del empleado.
        employee_code = data['header'].get('employee_code')
        if employee_code:
            partner = self._get_partner_employee_by_code(employee_code)
        # Proveedor genérico.
        if not partner:
            partner = self.env.company.pleo_partner_id

        if not partner:
            raise UserError('Debe indicar un proveedor genérico en la configuración del módulo para la '
                            'generación del reembolso pocket.')

        # Asiento del banco.
        # Líneas del asiento.
        lines = []
        # Haber
        line = {
            'account_id': data['header'].get('contra_account'),
            'partner_id': partner.id,
            'credit': data['header']['orig_amount']
        }
        lines.append([0, 0, line])
        # Debe
        line = {
            'account_id': partner.property_account_payable_id.id or None,
            'partner_id': partner.id,
            'debit': data['header']['orig_amount']
        }
        lines.append([0, 0, line])
        # Cabecera del asiento.
        vals = {
            'ref': data['header']['text'],
            'date': data['header']['date'],
            'journal_id': journal_bank_id.id,
            'partner_id': partner.id,
            'line_ids': lines
        }
        # Creo el asiento.
        account_move_bank = self.env['account.move'].create(vals)
        account_move_bank.action_post()

        # Concilio las líneas del asiento del banco con los gastos pocket pendientes de conciliar.
        account_move_lines = self.env['account.move.line'].search([('partner_id', '=', partner.id),
                                                                   ('is_pocket_move', '=', True),
                                                                   ('reconciled', '=', False),
                                                                   ('parent_state', '=', 'posted'),
                                                                   ('account_id', '=', partner.property_account_payable_id.id)])
        account_move_bank_lines = account_move_bank.line_ids.\
            filtered(lambda l: l.reconciled == False and l.account_id == partner.property_account_payable_id)
        (account_move_lines + account_move_bank_lines).reconcile()

    def process_records(self):
        """
        Procesa los registros seleccionados, generando las entradas correspondiente en la Contabilidad.
        Returns:

        """
        # Agrupo registros por receipt.
        receipts = self._get_receipts()
        for r in receipts:
            receipt = receipts[r]
            # Hay que determinar el tipo de documento a generar, tenemos las siguientes opciones:
            # 1) ticket (Factura de Proveedor)
            # 2) ticket
            # 3) ticket (Factura de Proveedor) con más de un IVA, clasifica como el punto 1
            # 4) Gastos Pocket (En Efectivo)
            # 5) Reembolso Pocket
            if receipt['tipo'] == 'factura':
                self.create_invoice(receipt)
            elif receipt['tipo'] == 'ticket':
                self.create_ticket(receipt)
            elif receipt['tipo'] == 'gasto_pocket':
                self.create_gasto_pocket(receipt)
            elif receipt['tipo'] == 'reembolso_pocket':
                self.create_reembolso_pocket(receipt)

    def process(self):
        """
        Procesa el registro de Pleo, generando los objetos correspondientes en el modelo de datos de Odoo.
        Returns:
        """
        # Controls
        self.controls()
        # Proceso
        self.process_records()
        # Actualiza estado
        self.state = 'realizado'
