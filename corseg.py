#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, If

__all__ = [
        'CiaSeguros', 'Ramo', 'CiaPoliza', 'Poliza',
        'Vendedor', 'TipoComision', 'TablaComisionVendedor',
        'FormaPago', 'FrecuenciaPago', 'Emision',
        'VehiculoMarca', 'VehiculoModelo',
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
    polizas = fields.One2Many('corseg.cia.poliza',
        'cia', 'Polizas')


class Ramo(ModelSQL, ModelView):
    'Ramo'
    __name__ = 'corseg.ramo'
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class CiaPoliza(ModelSQL, ModelView):
    'Poliza Compania de Seguros'
    __name__ = 'corseg.cia.poliza'
    name = fields.Char('Nombre', required=True)
    cia = fields.Many2One(
            'corseg.cia', 'Compania de Seguros', required=True)
    ramo = fields.Many2One(
            'corseg.ramo', 'Ramo', required=True)
    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision', required=False)  # TODO MultiValue - Depende de la company - Debe ser requerido
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
    cia = fields.Many2One(
            'corseg.cia', 'Compania de Seguros', required=True)
    cia_poliza = fields.Many2One(
            'corseg.cia.poliza', 'Poliza de la Compania', required=True)
    numero = fields.Char('Numero de Poliza', required=True)
    titular = fields.Many2One('party.party', 'Titular', required=True)
    emsiones = fields.One2Many('corseg.emision',
        'poliza', 'Emisiones')
    is_colectiva = fields.Boolean('Colectiva')
    state = fields.Selection(STATES, 'Estado', readonly=True, required=True)

    #TODO unique(cia_poliza, numero)

    @staticmethod
    def default_company():
        return Transaction().context.get('company')


class Vendedor(ModelSQL, ModelView):
    'Vendedor'
    __name__ = 'corseg.vendedor'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    # TODO alias - Caso Dafne
    tabla_comision = fields.One2Many('corseg.comision.vendedor',
        'vendedor', 'Tabla Comision')
    emisiones = fields.One2Many('corseg.emision',
        'vendedor', 'Polizas', readonly=True)
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
    pago_unico = fields.Boolean('Pago unico')
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class TablaComisionVendedor(ModelSQL, ModelView):
    'Tabla Comision Vendedor'
    __name__ = 'corseg.comision.vendedor'
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor',
        required=True, ondelete='CASCADE')
    poliza = fields.Many2One('corseg.cia.poliza',
        'Poliza', required=True)
    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision', required=True) # TODO MultiValue

    #TODO unique(vendedor, poliza)


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


class Emision(ModelSQL, ModelView):
    'Emision de Poliza'
    __name__ = 'corseg.emision'
    poliza = fields.Many2One(
            'corseg.poliza', 'Poliza', required=True)
    f_emision = fields.Date('Emitida el', required=True)
    f_desde = fields.Date('Desde', required=True)
    f_hasta = fields.Date('Hasta', required=True)
    suma_asegurada = fields.Numeric('Suma Asegurada', digits=(16, 2))
    prima = fields.Numeric('Prima', digits=(16, 2))
    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision', required=True)
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor', required=True)
    tipo_comision_vendedor = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision Vendedor', required=True)
    forma_pago = fields.Many2One('corseg.forma_pago', 'Forma pago', required=True)
    frecuencia_pago = fields.Many2One('corseg.frecuencia_pago',
        'Frecuencia pago', required=True)
    no_cuotas = fields.Integer('Cant. cuotas')
    state = fields.Selection(STATES, 'Estado', readonly=True, required=True)


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
