# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime

# class encargos(models.Model):
#     _name = 'encargos.encargos'
#     _description = 'encargos.encargos'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

class encargo(models.Model):
    _name="encargos.encargo"
    _description = "Gestiona los encargos realizados"
    _order = "Fecha_inicio desc, id desc"
    id_cliente = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True,
        domain =[('customer_rank','>',0)] #Solo clientes.Odoo unifica en res.partner clientes y proveedores,entre otros
    )
    Descripcion = fields.Char(string="Descripción del encargo",required=True)
    Fecha_inicio = fields.Date(string="Fecha de inicio del encargo",default=datetime.date.today())
    Fecha_fin = fields.Date(string="Fecha de finalización del encargo")
    materiales_ids = fields.One2many(
        'encargos.material',
        'encargo_id',
        string='Materiales'
    )

    costo_materiales = fields.Float()
    Horas_Realizadas = fields.Float(string="Horas totales invertidas en el encargo",compute="calcular_horas")
    @api.depends
    def calcular_horas(self):
        self.Horas_Realizadas = 0

        
    estado = fields.Selection([('c','Creado'),('i','En progreso'),('t','Terminado'),('e','Enviado')])
    #Metodo provisional por si hay que  implementar eventos al cambiar el encargo de estado
    def write(self,vals):
        if 'estado' in vals:
            pass
        return super().write(vals)
    



class Material(models.Model):
    _name="encargos.material"
    _description="Materiales usados en un encargo"

    encargo_id = fields.Many2one("encargos.encargo",string="Encargo")
    nombre_material = fields.Char(string="Material",required=True)
    precio = fields.Float(string="Precio unitario")
    cantidad = fields.Float(string="Cantidad de material usado en gramos",default=1.0)
    unidades_medida = fields.Selection([
        ('gramos','Gramos'),
        ('kilogramos','Kilogramos'),
        ('mililitros','Mililitros'),
        ('litros','Litros')
    ],string="Unidad de medida",default='mililitros')

    costo_total = fields.Float(string="Costo total de todos los materiales",compute="_calcular_costo",store=True)
    @api.depends('precio','cantidad')
    def _calcular_costo(self):
        for registro in self:
            registro.costo_total = registro.precio * registro.cantidad