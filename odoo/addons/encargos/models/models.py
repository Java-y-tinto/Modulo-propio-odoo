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
    #Para que Odoo me encuentre los encargos al crear sesiones y materiañes
    _rec_name = 'Descripcion'
    #Obtengo la moneda de Odoo puesta por el usuario
    currency_id = fields.Many2one(
    'res.currency',
    string='Moneda',
    default=lambda self: self.env.company.currency_id
    )

    id_cliente = fields.Many2one(
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
        # Solo validar si la fecha de fin está establecida manualmente
            if registro.Fecha_inicio and registro.Fecha_fin:
                if registro.Fecha_inicio > registro.Fecha_fin:
                    raise ValidationError('La fecha de inicio debe ser anterior a la de finalización')
            
    materiales_ids = fields.One2many(
        'encargos.material',
        'encargo_id',
        string='Materiales',
        required=True
    )

    #Sesiones dedicadas a un encargo
    sesion_ids = fields.One2many(
        'encargos.sesion',
        'encargo_id',
        string='Sesiones'
    )

    costo_materiales = fields.Monetary(
        string="Costo total de materiales",
        compute="_calcular_costo_materiales",
        store=True,
        currency_field='currency_id'
    )
    #Calculo el costo total de los materiales a partir del campo "costo_total" de las clases
    @api.depends('materiales_ids.costo_total')
    def _calcular_costo_materiales(self):
        for registro in self:
            registro.costo_materiales = sum(registro.materiales_ids.mapped('costo_total'))

    Precio_hora = fields.Monetary(string="Precio por hora del encargo",required=True,currency_field='currency_id')
    Horas_Realizadas = fields.Float(string="Horas totales invertidas en el encargo",compute="calcular_horas")
    #Metodo que calcula el total de horas realizadas teniendo en cuenta las sesiones
    @api.depends('sesion_ids.Horas_sesion')
    def calcular_horas(self):
        for registro in self:
        #Suma de todas las horas de las sesiones
            registro.Horas_Realizadas = sum(registro.sesion_ids.mapped('Horas_sesion'))

        
    estado = fields.Selection([('c','Creado'),('i','En progreso'),('t','Terminado'),('e','Enviado')],default='c',string="Estado del encargo",group_expand='_mostrar_todas_columnas')
    @api.model
    def _mostrar_todas_columnas(self,estado,dominio,orden=None):
        #Muestro todos los estados siempre
        return ['c','i','t','e']
    #Metodo que se ejecuta cuando un encargo cambia de estado
    def write(self,vals):
      # Si el estado cambia a 'Terminado' y no hay fecha de fin, establecer la fecha actual
        if vals.get('estado') == 't' and not self.Fecha_fin:
            vals['Fecha_fin'] = fields.Date.today()
    # Si el estado cambia a un estado que no es 'Terminado' o 'Enviado', borrar la fecha de fin
        elif vals.get('estado') in ['c', 'i'] and self.Fecha_fin:
            vals['Fecha_fin'] = False
        

        return super().write(vals)
    
    #llamada al metodo encargado de crear la factura
    def crear_factura(self):
        return self.env['account.move'].crear_factura_desde_encargo(self)
    



class Material(models.Model):
    _name="encargos.material"
    _description="Materiales usados en un encargo"
    _rec_name='nombre_material'

    #Relaciono con encargos
    encargo_id = fields.Many2one(
        'encargos.encargo',
        string='Encargo'
    )

    #Relaciono con el modulo de productos para evitar duplicidades
    product_id = fields.Many2one(
        'product.product',
        string='Producto del catálogo',
        help='Selecciona un producto existente del catálogo',
        #Si se borra el producto,se borra el material
        ondelete='cascade'
    )

    #Campos especificos del material
    nombre_material = fields.Char(
        string="Material", 
        compute="_compute_nombre_material",
        store=True
    )
    
    precio_unitario = fields.Monetary(
        string="Precio unitario",
        compute="_compute_precio_unitario",
        store=True,
        currency_field='currency_id'
    )

    unidades_medida = fields.Selection([
        ('gramos', 'Gramos'),
        ('kilogramos', 'Kilogramos'),
        ('mililitros', 'Mililitros'),
        ('litros', 'Litros'),
        ('unidades', 'Unidades')
    ], string="Unidad de medida", default='mililitros')
    
    # Cantidad usada en este encargo
    cantidad = fields.Float(
        string="Cantidad usada", 
        default=1.0
    )
    
    # Costo calculado
    costo_total = fields.Monetary(
        string="Costo total",
        compute="_calcular_costo",
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Moneda',
        related='encargo_id.currency_id',
        store=True,
        readonly=True
    )
    
    # Campos computados para sincronizar con productos
    @api.depends('product_id', 'product_id.name')
    def _compute_nombre_material(self):
        for registro in self:
            if registro.product_id:
                registro.nombre_material = registro.product_id.name
    
    @api.depends('product_id', 'product_id.list_price')
    def _compute_precio_unitario(self):
        for registro in self:
            if registro.product_id:
                registro.precio_unitario = registro.product_id.list_price
    
    @api.depends('product_id', 'product_id.uom_id')
    def _compute_unidad_medida(self):
        for registro in self:
            #Para registrar la unidad de medida que usa el producto
            if registro.product_id and registro.product_id.uom_id:
                registro.unidad_medida_id = registro.product_id.uom_id.id
    
    @api.depends('precio_unitario', 'cantidad')
    def _calcular_costo(self):
        for registro in self:
            registro.costo_total = registro.precio_unitario * registro.cantidad


#Clase que modela las sesiones de trabajo
class Sesion(models.Model):
    _name="encargos.sesion"
    _description="Administra las sesiones de trabajo dedicadas a un encargo"

    encargo_id = fields.Many2one('encargos.encargo',
    string="Encargo al que se le dedica la sesion",
    required=True,
    ondelete='cascade',
    #Mostrar solo encargos no enviados
    domain = [('estado','in',['c','i','t'])]
    )
    Fecha_inicio = fields.Date(string='Fecha de inicio de la sesión',default = datetime.date.today())
    Fecha_fin = fields.Date(string="Fecha de finalización de la sesión de trabajo",required=False)
    @api.constrains('encargo_id.Fecha_inicio', 'Fecha_inicio', 'Fecha_fin')
    def _comprobar_fecha(self):
        for registro in self:
            # Verificar que la fecha de inicio de la sesión no sea anterior a la fecha de inicio del encargo
            if registro.encargo_id and registro.encargo_id.Fecha_inicio and registro.Fecha_inicio:
                if registro.Fecha_inicio < registro.encargo_id.Fecha_inicio:
                    raise ValidationError("La fecha de inicio de la sesión no puede ser anterior a la de creación del encargo")
        
            # Verificar que la fecha de fin no sea anterior a la fecha de inicio (solo si la fecha de fin está establecida)
            if registro.Fecha_fin and registro.Fecha_inicio:
                if registro.Fecha_fin < registro.Fecha_inicio:
                    raise ValidationError("La fecha de finalización no puede ser anterior a la fecha de inicio")

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
    encargo_id = fields.Many2one('encargos.encargo',string="Encargo facturado")
 
    #Metodo que crea una factura desde un encargo
    @api.model
    def crear_factura_desde_encargo(self,encargo:encargo):
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
                'price_unit': material.precio_unitario
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