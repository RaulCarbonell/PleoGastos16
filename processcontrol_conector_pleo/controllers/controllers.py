# -*- coding: utf-8 -*-
# from odoo import http


# class ProcesscontrolConectorPleo(http.Controller):
#     @http.route('/processcontrol_conector_pleo/processcontrol_conector_pleo/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/processcontrol_conector_pleo/processcontrol_conector_pleo/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('processcontrol_conector_pleo.listing', {
#             'root': '/processcontrol_conector_pleo/processcontrol_conector_pleo',
#             'objects': http.request.env['processcontrol_conector_pleo.processcontrol_conector_pleo'].search([]),
#         })

#     @http.route('/processcontrol_conector_pleo/processcontrol_conector_pleo/objects/<model("processcontrol_conector_pleo.processcontrol_conector_pleo"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('processcontrol_conector_pleo.object', {
#             'object': obj
#         })
