#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields
from trytond.pyson import Eval, If
from trytond.modules.company.model import (
        CompanyMultiValueMixin, CompanyValueMixin)

__all__ = [
        'Asegurado', 'Beneficiario', 'Certificado',
        'CiaProducto', 'CiaSeguros',
        'ComisionCia', 'CiaTipoComision',
        'ComisionVendedor', 'VendedorTipoComision',
        'FormaPago', 'FrecuenciaPago', 'GrupoPoliza',
        'Movimiento', 'Poliza', 'Ramo', 'TipoComision',
        'VehiculoMarca', 'VehiculoModelo', 'Vendedor',
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

    def get_rec_name(self, name):
        return self.party.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('party.rec_name',) + tuple(clause[1:])]


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


class ComisionCia(ModelSQL, ModelView, CompanyMultiValueMixin):
    'Tabla Comision Cia'
    __name__ = 'corseg.comision.cia'
    producto = fields.Many2One('corseg.cia.producto',
        'Producto', required=True)
    renovacion = fields.Integer('Renovacion', required=True)
    tipo_comision = fields.MultiValue(fields.Many2One('corseg.tipo_comision',
            'Tipo Comision', required=True))
    tipo_cia_comision = fields.One2Many(
        'corseg.cia.tipo_comision', 'comision_cia', 'Tipo Comision')
    re_renovacion = fields.Boolean('Recurrente en renovacion',
        help="Hacer esta comision recurrente en las proximas renovaciones.")
    re_cuota = fields.Boolean('Recurrente en cuotas',
        help="Hacer esta comision recurrente en todas las cuotas.")

    # TODO test tipo_comision
    # TODO order by renovacion
    # TODO defualt recurrente = True

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'tipo_comision'}:
            return pool.get('corseg.cia.tipo_comision')
        return super(ComisionCia, cls).multivalue_model(field)


class CiaTipoComision(ModelSQL, CompanyValueMixin):
    "Cia Tipo Comision"
    __name__ = 'corseg.cia.tipo_comision'
    comision_cia = fields.Many2One(
        'corseg.comision.cia', 'Comision Cia',
        ondelete='CASCADE', select=True)
    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision', required=True)


class ComisionVendedor(ModelSQL, ModelView, CompanyMultiValueMixin):
    'Tabla Comision Vendedor'
    __name__ = 'corseg.comision.vendedor'
    producto = fields.Many2One('corseg.cia.producto',
        'Producto', required=True)
    cia_name = fields.Function(fields.Char('Cia'), 'get_cia_name')
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor',
        required=True, ondelete='CASCADE')
    renovacion = fields.Integer('Renovacion', required=True)
    tipo_comision = fields.MultiValue(fields.Many2One('corseg.tipo_comision',
            'Tipo Comision', required=True))
    tipo_vendedor_comision = fields.One2Many(
        'corseg.vendedor.tipo_comision', 'comision_vendedor', 'Tipo Comision')
    re_renovacion = fields.Boolean('Recurrente en renovacion',
        help="Hacer esta comision recurrente en las proximas renovaciones.")
    re_cuota = fields.Boolean('Recurrente en cuotas',
        help="Hacer esta comision recurrente en todas las cuotas.")

    # TODO order by vendedor, renovacion

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'tipo_comision'}:
            return pool.get('corseg.vendedor.tipo_comision')
        return super(ComisionVendedor, cls).multivalue_model(field)

    def get_cia_name(self, name):
        if self.producto:
            return self.producto.cia.rec_name


class VendedorTipoComision(ModelSQL, CompanyValueMixin):
    "Vendedor Tipo Comision"
    __name__ = 'corseg.vendedor.tipo_comision'
    comision_vendedor = fields.Many2One(
        'corseg.comision.vendedor', 'Comision Vendedor',
        ondelete='CASCADE', select=True)
    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision', required=True)


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
    pagos = fields.Numeric('Pagos', digits=(16, 2))
    # TODO function -> saldo = fields.Numeric('Saldo', digits=(16, 2))
    forma_pago = fields.Many2One('corseg.forma_pago', 'Forma pago', required=True)
    frecuencia_pago = fields.Many2One('corseg.frecuencia_pago',
        'Frecuencia pago', required=True)
    no_cuotas = fields.Integer('Cant. cuotas')

    tipo_comision = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision')
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor', required=True)
    tipo_comision_vendedor = fields.Many2One('corseg.tipo_comision',
        'Tipo Comision Vendedor')

    certificados = fields.One2Many('corseg.poliza.certificado',
        'certificado', 'Certificados')
    movimientos = fields.One2Many('corseg.poliza.movimiento',
        'poliza', 'Historia')
    # TODO pagos
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

    def get_rec_name(self, name):
        return self.party.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('party.rec_name',) + tuple(clause[1:])]


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

    def get_rec_name(self, name):
        return self.party.rec_name

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('party.rec_name',) + tuple(clause[1:])]


class Vendedor(ModelSQL, ModelView):
    'Vendedor'
    __name__ = 'corseg.vendedor'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    alias = fields.Char('Alias')
    comision = fields.One2Many('corseg.comision.vendedor',
        'vendedor', 'Tabla Comision', readonly=True)
    emisiones = fields.One2Many('corseg.emision',
        'vendedor', 'Polizas', readonly=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True

    def get_rec_name(self, name):            
        return self.party.rec_name if not self.alias else self.alias

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = ['OR']
        domain.append(('party.rec_name', clause[1], clause[2]))
        domain.append(('alias', clause[1], clause[2]))
        return domain


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
    # TODO tipo: nueva, renovacion, finiquito, endoso, ajuste_prima_suma_asegurada
    suma_asegurada = fields.Numeric('Suma Asegurada', digits=(16, 2))
    prima = fields.Numeric('Prima', digits=(16, 2))
    # TODO inclusion
    # TODO exclusion

    # TODO order by fecha


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
