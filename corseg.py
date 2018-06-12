#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pyson import Eval, If, Bool, Equal, Not, In
from trytond.modules.company.model import (
        CompanyMultiValueMixin, CompanyValueMixin)
from decimal import Decimal

__all__ = [
        'CiaProducto', 'CiaSeguros', 'Origen',
        'ComisionCia', 'CiaTipoComision',
        'ComisionVendedor', 'VendedorTipoComision',
        'FormaPago', 'FrecuenciaPago', 'GrupoPoliza',
        'Poliza', 'Ramo', 'TipoComision', 'Comentario',
        'Vendedor',
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

    # TODO order by renovacion

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
    parent = fields.Many2One('corseg.poliza.grupo', 'Parent', select=True)
    childs = fields.One2Many('corseg.poliza.grupo',
        'parent', 'Children', readonly=True)
    polizas = fields.One2Many('corseg.poliza',
        'grupo', 'Polizas', readonly=True)
    description = fields.Char('Descripcion', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    def get_rec_name(self, name):
        if self.parent:
            return self.parent.get_rec_name(name) + '/' + self.name
        return self.name


class Origen(ModelSQL, ModelView):
    'Origen Poliza'
    __name__ = 'corseg.poliza.origen'
    name = fields.Char('Nombre', required=True)
    notas = fields.Text('Notas', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class Poliza(ModelSQL, ModelView):
    'Poliza de seguros'
    __name__ = 'corseg.poliza'
    company = fields.Many2One('company.company', 'Company', required=False, # TODO required=True
        states={
            'readonly': True,
            },
        domain=[ # TODO habilitar el domain al terminar la migracion
#            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
#                Eval('context', {}).get('company', -1)),
            ], select=True)
    currency = fields.Many2One('currency.currency', 'Moneda', required=False, # TODO required=True
        states={
            'readonly': True,
            })
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'on_change_with_currency_digits')
    grupo = fields.Many2One(
            'corseg.poliza.grupo', 'Grupo',
            domain=[('company', '=', Eval('company'))],
            depends=['company']
        )
    cia = fields.Many2One('corseg.cia',
        'Compania de Seguros', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['new'])),
            },
        depends=['state'])
    cia_producto = fields.Many2One('corseg.cia.producto',
        'Producto', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['new'])),
            },
        domain=[
            If(
                Bool(Eval('cia')),
                [('cia', '=', Eval('cia'))], []
            )
        ],
        depends=['cia', 'state'])
    ramo = fields.Function(fields.Char('Ramo'),
        'get_ramo')
    numero = fields.Char('Numero de Poliza', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['new'])),
            },
        depends=['state'])
    origen = fields.Many2One('corseg.poliza.origen', 'Origen',
        states={
            'readonly': Not(In(Eval('state'), ['new'])),
            },
        depends=['state'])
    contratante = fields.Many2One('party.party', 'Contratante', readonly=True)
    f_emision = fields.Date('Emitida el',  readonly=True)
    f_desde = fields.Date('Desde',  readonly=True)
    f_hasta = fields.Date('Hasta',  readonly=True)
    suma_asegurada = fields.Numeric('Suma Asegurada',
        digits=(16, Eval('currency_digits', 2)), readonly=True,
        depends=['currency_digits'])
    prima = fields.Numeric('Prima',
        digits=(16, Eval('currency_digits', 2)), readonly=True,
        depends=['currency_digits'])
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor', readonly=True)
    notas = fields.Text('Notas', size=None)
    forma_pago = fields.Many2One('corseg.forma_pago', 'Forma pago',  readonly=True)
    frecuencia_pago = fields.Many2One('corseg.frecuencia_pago',
        'Frecuencia pago',  readonly=True)
    no_cuotas = fields.Integer('Cant. cuotas', readonly=True)
    monto_pago = fields.Function(fields.Numeric(
            'Pagado', digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_monto_pago')
    saldo = fields.Function(fields.Numeric(
            'Saldo', digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_saldo')

#   TODO comision_cia
#   TODO comision_vendedor

    certificados_in = fields.One2Many('corseg.poliza.certificado',
        'poliza', 'Incluidos', readonly=True,
        filter=[('state', '=', 'incluido')])
    certificados_ex = fields.One2Many('corseg.poliza.certificado',
        'poliza', 'Excluidos', readonly=True,
        filter=[('state', '=', 'excluido')])
    movimientos = fields.One2Many('corseg.poliza.movimiento',
        'poliza', 'Movimientos', readonly=True)
    pagos = fields.One2Many('corseg.poliza.pago',
        'poliza', 'Pagos',
        states={
            'invisible': Equal(Eval('state'), 'new'),
            },
        depends=['state'])
    comentarios = fields.One2Many('corseg.poliza.comentario',
        'poliza', 'Comentarios')

    # TODO renovacion - readonly, empieza en 0 para polizas nuevas
    
    state = fields.Selection([
            ('new', 'Nuevo'),
            ('vigente', 'Vigente'),
            ('cancelada', 'Cancelada'),
        ],
        'Estado', readonly=True, required=True)

    @classmethod
    def __setup__(cls):
        super(Poliza, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('cia_product_numero_uniq', 
                Unique(t, t.cia_producto, t.numero),
                'El numero de poliza ya existe para este producto'),
        ]

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_state():
        return 'new'

    @staticmethod
    def default_currency():
        Company = Pool().get('company.company')
        company = Transaction().context.get('company')
        if company:
            company = Company(company)
            return company.currency.id

    @staticmethod
    def default_currency_digits():
        Company = Pool().get('company.company')
        company = Transaction().context.get('company')
        if company:
            company = Company(company)
            return company.currency.digits
        return 2

    def get_rec_name(self, name):
        return self.cia.rec_name + ' / ' + self.numero

    @classmethod
    def search_rec_name(cls, name, clause):
        domain = ['OR']
        domain.append(('cia.rec_name', clause[1], clause[2]))
        domain.append(('numero', clause[1], clause[2]))
        return domain

    @fields.depends('company', 'cia', 'cia_producto')
    def on_change_company(self):
        self.cia = None
        self.cia_producto = None
        if self.company:
            self.currency = self.company.currency

    @fields.depends('cia_producto')
    def on_change_cia(self):
        self.cia_producto = None

    @fields.depends('cia', 'cia_producto', 'ramo')
    def on_change_cia_producto(self):
        self.ramo = None
        if self.cia_producto:
            self.cia = self.cia_producto.cia
            self.ramo = self.cia_producto.ramo.rec_name

    @fields.depends('currency')
    def on_change_with_currency_digits(self, name=None):
        if self.currency:
            return self.currency.digits
        return 2

    def get_ramo(self, name):
        if self.cia_producto:
            return self.cia_producto.ramo.rec_name

    def get_monto_pago(self, name):
        res = Decimal(0)
        if self.pagos:
            for pago in self.pagos:
                if pago.state == 'confirmado':
                    res += pago.monto
        return res

    def get_saldo(self, name):
        res = Decimal(0)
        if self.prima:
            return self.prima - self.monto_pago
        return res


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


class Comentario(ModelSQL, ModelView):
    'Comentarios sobre la Poliza'
    __name__ = 'corseg.poliza.comentario'
    poliza = fields.Many2One(
        'corseg.poliza', 'Poliza', required=True)
    fecha = fields.Date('Fecha', required=True)
    comentario = fields.Text('Comentario', size=None)
    user_name = fields.Function(fields.Char('Usuario'),
        'get_user_name')

    def get_user_name(self, name):
        if self.create_uid:
            return self.create_uid.rec_name

    # TODO order_by fecha


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
