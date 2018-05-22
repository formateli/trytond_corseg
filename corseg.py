#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, If

__all__ = [
        'Asegurado', 'Beneficiario', 'Certificado',
        'CiaProducto', 'CiaSeguros', 'ComisionCia',
        'ComisionVendedor', 'FormaPago', 'FrecuenciaPago',
        'GrupoPoliza', 'Movimiento', 'Poliza', 'Ramo',
        'TipoComision', 'VehiculoMarca', 'VehiculoModelo',
        'Vendedor',
    ]

STATES = [
    ('nuevo', 'Nuevo'),
    ('renovado', 'Renovado'),
    ('moroso', 'Moroso'),
    ('cancelado', 'Cancelado'),
    ('reconsideracion', 'En Reconsideracion'),
    ('suspendido', 'Suspendido'),
    ('reactivado', 'Reactivado'),
]


class CiaSeguros(ModelSQL, ModelView):
    'Compania de Seguros'
    __name__ = 'corseg.cia'
    party = fields.Many2One('party.party', 'Entidad', required=True,
            ondelete='CASCADE')
    productos = fields.One2Many('corseg.cia.producto',
        'cia', 'Productos')
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class Ramo(ModelSQL, ModelView):
    'Ramo'
    __name__ = 'corseg.ramo'
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class TipoComision(ModelSQL, ModelView):
    'Tipo Comision'
    __name__ = 'corseg.tipo_comision'
    name = fields.Char('Nombre', required=True)
    tipo = fields.Selection([
            ('fijo', 'Monto Fijo'),
            ('porcentaje', 'Porcentaje'),
        ], 'Tipo', required=True)
    monto = fields.Numeric('Monto', digits=(16, 2))
    description = fields.Char('Descripcion', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class CiaProducto(ModelSQL, ModelView):
    'Producto Compania de Seguros'
    __name__ = 'corseg.cia.producto'
    name = fields.Char('Nombre', required=True)
    cia = fields.Many2One(
            'corseg.cia', 'Compania de Seguros', required=True)
    ramo = fields.Many2One(
            'corseg.ramo', 'Ramo', required=True)
    comision_cia = fields.One2Many('corseg.comision.cia',
        'producto', 'Tabla Comision')
    comision_vendedor = fields.One2Many('corseg.comision.vendedor',
        'producto', 'Tabla Comision Vendedor')
    es_colectiva = fields.Boolean('Colectiva')
    description = fields.Text('Descripcion', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class ComisionCia(ModelSQL, ModelView):
    'Tabla Comision Cia'
    __name__ = 'corseg.comision.cia'
    producto = fields.Many2One('corseg.cia.producto',
        'Producto', required=True)
    renovacion = fields.Integer('Renovacion', required=True)
    # TODO tipo_comision - MultiValue
    re_renovacion = fields.Boolean('Recurrente en renovacion',
        help="Hacer esta comision recurrente en las proximas renovaciones.")
    re_cuota = fields.Boolean('Recurrente en cuotas',
        help="Hacer esta comision recurrente en todas las cuotas.")

    # TODO order by renovacion
    # TODO defualt recurrente = True


class ComisionVendedor(ModelSQL, ModelView):
    'Tabla Comision Vendedor'
    __name__ = 'corseg.comision.vendedor'
    producto = fields.Many2One('corseg.cia.producto',
        'Producto', required=True)
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor',
        required=True, ondelete='CASCADE')
    renovacion = fields.Integer('Renovacion', required=True)
    # TODO tipo_comision - MultiValue
    re_renovacion = fields.Boolean('Recurrente en renovacion',
        help="Hacer esta comision recurrente en las proximas renovaciones.")
    re_cuota = fields.Boolean('Recurrente en cuotas',
        help="Hacer esta comision recurrente en todas las cuotas.")

    # TODO order by vendedor, renovacion


class GrupoPoliza(ModelSQL, ModelView):
    'Grupo de Polizas'
    __name__ = 'corseg.poliza.grupo'
    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    name = fields.Char('Nombre', required=True)
    polizas = fields.One2Many('corseg.poliza',
        'grupo', 'Polizas',
        domain=[
            ('company', '=', Eval('company'))
        ], depends=['company'])
    description = fields.Char('Descripcion', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class Poliza(ModelSQL, ModelView):
    'Poliza de seguros'
    __name__ = 'corseg.poliza'
    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    grupo = fields.Many2One(
            'corseg.poliza.grupo', 'Grupo',
            domain=[('company', '=', Eval('company'))],
            depends=['company'] 
        )
    cia = fields.Many2One(
            'corseg.cia', 'Compania de Seguros', required=True)
    cia_producto = fields.Many2One(
            'corseg.cia.producto', 'Producto Cia Seguro', required=True)
    numero = fields.Char('Numero de Poliza', required=True)
    contratante = fields.Many2One('party.party', 'Contratante', required=True)
    f_emision = fields.Date('Emitida el', required=True)
    f_desde = fields.Date('Desde', required=True)
    f_hasta = fields.Date('Hasta', required=True)
    suma_asegurada = fields.Numeric('Suma Asegurada', digits=(16, 2))
    prima = fields.Numeric('Prima', digits=(16, 2))
    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision')
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor', required=True)
    tipo_comision_vendedor = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision Vendedor')
    forma_pago = fields.Many2One('corseg.forma_pago', 'Forma pago', required=True)
    frecuencia_pago = fields.Many2One('corseg.frecuencia_pago',
        'Frecuencia pago', required=True)
    no_cuotas = fields.Integer('Cant. cuotas')
    certificados = fields.One2Many('corseg.poliza.certificado',
        'certificado', 'Certificados')
    movimientos = fields.One2Many('corseg.poliza.movimiento',
        'poliza', 'Historia')
    notas = fields.Char('Notas', size=None)

    # TODO renovacion - function field, empieza en 0 para polizas nuevas
    
    # cancelada, suspendida, morosa, activa, renovada, reactivada
    state = fields.Selection(STATES, 'Estado', readonly=True, required=True)

    #TODO unique(cia_producto, numero)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class Certificado(ModelSQL, ModelView):
    'Certificado'
    __name__ = 'corseg.poliza.certificado'
    poliza = fields.Many2One(
            'corseg.poliza', 'Poliza', required=True)
    numero = fields.Char('Numero de Certificado', required=True)
    asegurado = fields.Many2One('corseg.poliza.asegurado', 'Asegurado', required=True,
            ondelete='CASCADE')
    beneficiarios = fields.One2Many('corseg.poliza.beneficiario',
        'certificado', 'Beneficiarios')
    notas = fields.Char('Notas', size=None)
    # TODO datos tecnicos
    # TODO inclusion, exclusion ? seria el id del movimiento
    # TODO state : activo, excluido


class Asegurado(ModelSQL, ModelView):
    'Asegurado'
    __name__ = 'corseg.poliza.asegurado'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    certificados = fields.One2Many('corseg.poliza.certificado',
        'asegurado', 'Certificados', readonly=True)
    # TODO siniestros


class Beneficiario(ModelSQL, ModelView):
    'Beneficiario / Dependiente'
    __name__ = 'corseg.poliza.beneficiario'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    certificado = fields.Many2One(
            'corseg.poliza.certificado', 'Certificado', required=True)
    # TODO parentesco
    # TODO inclusion, exclusion ? seria el id del movimiento
    # TODO state : activo, excluido


class Vendedor(ModelSQL, ModelView):
    'Vendedor'
    __name__ = 'corseg.vendedor'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    # TODO alias - Caso Dafne
    comision = fields.One2Many('corseg.comision.vendedor',
        'vendedor', 'Tabla Comision', readonly=True)
    emisiones = fields.One2Many('corseg.emision',
        'vendedor', 'Polizas', readonly=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class FormaPago(ModelSQL, ModelView):
    'Tipo Pago'
    __name__ = 'corseg.forma_pago'
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class FrecuenciaPago(ModelSQL, ModelView):
    'Frecuencia Pago'
    __name__ = 'corseg.frecuencia_pago'
    name = fields.Char('Nombre', required=True)
    meses = fields.Integer('Meses', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class Movimiento(ModelSQL, ModelView):
    'Movimiento de Poliza'
    __name__ = 'corseg.poliza.movimiento'
    poliza = fields.Many2One(
            'corseg.poliza', 'Poliza', required=True)
    fecha = fields.Date('Fecha', required=True)
    # TODO tipo: nueva, renovacion, finiquito, endoso
    suma_asegurada = fields.Numeric('Suma Asegurada', digits=(16, 2))
    prima = fields.Numeric('Prima', digits=(16, 2))
    # TODO inclusion
    # TODO exclusion


class VehiculoMarca(ModelSQL, ModelView):
    'Ramo'
    __name__ = 'corseg.vehiculo.marca'
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class VehiculoModelo(ModelSQL, ModelView):
    'Ramo'
    __name__ = 'corseg.vehiculo.modelo'
    name = fields.Char('Nombre', required=True)
    marca = fields.Many2One('corseg.vehiculo.marca', 'Marca', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True
