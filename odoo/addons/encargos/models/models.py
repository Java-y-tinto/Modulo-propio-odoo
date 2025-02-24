# -*- coding: utf-8 -*-

from odoo import models, fields, api
import datetime
from odoo.exceptions import ValidationError
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
    id_cliente = fields.Many2One(
        'res.partner',
        string='Cliente',
        required=True,
        domain =[('customer_rank','>',0)] #Solo clientes.Odoo unifica en res.partner clientes y proveedores,entre otros
    )
    Descripcion = fields.Char(string="Descripción del encargo",required=True)
    Fecha_inicio = fields.Date(string="Fecha de inicio del encargo",default=datetime.date.today())
    Fecha_fin = fields.Date(string="Fecha de finalización del encargo")
    @api.constrains('Fecha_inicio','Fecha_fin')
    def _comprobar_fecha(self):
        for registro in self:
            if registro.Fecha_inicio > registro.Fecha_fin:
                raise ValidationError('La fecha de inicio debe ser anterior a la de finalización')
            
    materiales_ids = fields.One2many(
        'encargos.material',
        'encargo_id',
        string='Materiales'
    )

    #Sesiones dedicadas a un encargo
    sesion_ids = fields.One2Many(
        'encargos.sesion',
        'encargo_id',
        string='Sesiones'
    )

    costo_materiales = fields.Monetary(
        string="Costo total de materiales",
        compute="_calcular_costo_materiales",
        store=True
    )
    @api.depends('materiales_ids.costo_total')
    def _calcular_costo_materiales(self):
        for registro in self:
            registro.costo_materiales = sum(registro.materiales_ids.mapped('costo_total'))

    Precio_hora = fields.Monetary(string="Precio por hora del encargo",required=True)
    Horas_Realizadas = fields.Float(string="Horas totales invertidas en el encargo",compute="calcular_horas")
    #Metodo que calcula el total de horas realizadas teniendo en cuenta las sesiones
    @api.depends('sesion_ids.Horas_sesion')
    def calcular_horas(self):
        for registro in self:
        #Suma de todas las horas de las sesiones
            registro.Horas_Realizadas = sum(registro.sesion_ids.mapped('Horas_sesion'))

        
    estado = fields.Selection([('c','Creado'),('i','En progreso'),('t','Terminado'),('e','Enviado')])
    #Metodo provisional por si hay que  implementar eventos al cambiar el encargo de estado
    def write(self,vals):
        if 'estado' in vals:
            pass
        return super().write(vals)
    
    #llamada al metodo encargado de crear la factura
    def crear_factura(self):
        return self.env['account.move'].crear_factura_desde_encargo(self)
    


#Optamos por una clase aparte para que el usuario pueda crear sus propios materiales sin depender del modulo fabricacion
class Material(models.Model):
    _name="encargos.material"
    _description="Materiales usados en un encargo"

    encargo_id = fields.Many2One("encargos.encargo",string="Encargo")
    nombre_material = fields.Char(string="Material",required=True)
    precio = fields.Monetary(string="Precio unitario")
    cantidad = fields.Float(string="Cantidad de material usado en gramos",default=1.0)
    unidades_medida = fields.Selection([
        ('gramos','Gramos'),
        ('kilogramos','Kilogramos'),
        ('mililitros','Mililitros'),
        ('litros','Litros')
    ],string="Unidad de medida",default='mililitros')

    costo_total = fields.Monetary(string="Costo total de todos los materiales",compute="_calcular_costo",store=True)
    @api.depends('precio','cantidad')
    def _calcular_costo(self):
        for registro in self:
            registro.costo_total = registro.precio * registro.cantidad

#Clase que modela las sesiones de trabajo
class Sesion(models.Model):
    _name="encargos.sesion"
    _description="Administra las sesiones de trabajo dedicadas a un encargo"

    encargo_id = fields.Many2one('encargos.encargo',string="Encargo al que se le dedica la sesion")
    Fecha_inicio = fields.Date(string='Fecha de inicio de la sesión',default = datetime.date.today())
    Fecha_fin = fields.Date(string="Fecha de finalización de la sesión de trabajo")
    @api.constrains('encargo_id.Fecha_inicio','Fecha_inicio','Fecha_fin')
    def _comprobar_fecha(self):
        for registro in self:
            if registro.encargo_id.Fecha_inicio < registro.Fecha_inicio:
                raise ValidationError("La fecha de inicio de la sesion no puede ser anterior a la de creación del encargo")
            if registro.Fecha_fin < registro.Fecha_inicio:
                raise ValidationError("La fecha de inicio no puede ser anterior a la de fin")

    Horas_sesion = fields.Float(string="Horas dedicadas a la sesión")
    Etapa = fields.Selection([('c','concepto'),('b','boceto'),('i','en progreso'),('f','finalizado')])
    Notas = fields.Char(string="Notas de la sesion",required=False)
    #Archivo de imagen para guardar las fotos del progreso
    Foto_del_progreso = fields.Binary(string="Foto del progreso realizado en la sesion",required=True)


#Clase que se encarga de hacer las facturas que hereda de Encargo
class Factura(models.Model):
    #Heredo de facturacion
    _inherit = "account.move"

   #Relaciono factura con encargo
    encargo_id = fields.Many2One('encargos.encargo',string="Encargo facturado")
 
    #Metodo que crea una factura desde un encargo
    @api.model
    def crear_factura_desde_encargo(self,encargo:encargo):
        """
        Método específico que se encarga de crear facturas desde encargos
        """
        #Array que almacena las lineas de la factura
        lineas_factura = []

        #Linea para la descripcion del encargo
        if (encargo.Horas_Realizadas > 0):
            lineas_factura.append((0,0,{
                'name': f'Horas de trabajo realizadas para el encargo: {encargo.Descripcion}',
                'quantity': encargo.Horas_Realizadas,
                'price_unit': encargo.Precio_hora
            }))

        #Lineas para los materiales usados
        for material in encargo.materiales_ids:
            lineas_factura.append((0,0,{
                'name': f'Material: {material.nombre_material}',
                'quantity': material.cantidad,
                'price_unit': material.precio
            }))
        
        #Creo la factura
        vals = {
            #A quien se le hace la factura
            'partner_id': encargo.id_cliente.id,
            #Tipo de factura
            'move_type': 'out_invoice', #Factura de venta
            'invoice_line_ids': lineas_factura, #Array que representa las lineas de la factura
            'encargo_id': encargo.id, #Encargo del que se esta haciendo la factura
        }
        factura = self.create(vals)
        #Hago que Odoo abra la factura para que el usuario pueda editarla
        #Esto se llama acción 
        #https://www.odoo.com/documentation/18.0/es/developer/reference/backend/actions.html 

        return {
            'name': 'Factura de Cliente',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': factura.id,
            'type': 'ir.actions.act_window',
        }