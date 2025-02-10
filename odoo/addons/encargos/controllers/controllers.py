# -*- coding: utf-8 -*-
# from odoo import http


# class Encargos(http.Controller):
#     @http.route('/encargos/encargos', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/encargos/encargos/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('encargos.listing', {
#             'root': '/encargos/encargos',
#             'objects': http.request.env['encargos.encargos'].search([]),
#         })

#     @http.route('/encargos/encargos/objects/<model("encargos.encargos"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('encargos.object', {
#             'object': obj
#         })

