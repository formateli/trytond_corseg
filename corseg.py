#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.model import ModelView, ModelSQL, fields, Unique
from trytond.pyson import Eval, If, Bool, Equal, Not, In
from trytond.modules.company.model import CompanyMultiValueMixin
from decimal import Decimal

__all__ = [
        'Ramo',
        'CiaSeguros',
        'CiaProducto',
        'OrigenPoliza',
        'GrupoPoliza',
        'ComentarioPoliza',
        'Poliza',
        'Vendedor',
    ]


class Ramo(ModelSQL, ModelView):
    'Ramo'
    __name__ = 'corseg.ramo'
    name = fields.Char('Nombre', required=True)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class CiaSeguros(ModelSQL, ModelView):
    'Compania de Seguros'
    __name__ = 'corseg.cia'
    party = fields.Many2One('party.party', 'Entidad', required=True,
        ondelete='CASCADE',
        states={
            'readonly': Bool(Eval('productos')),
        }, depends=['productos'])
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


class CiaProducto(ModelSQL, ModelView, CompanyMultiValueMixin):
    'Producto Compania de Seguros'
    __name__ = 'corseg.cia.producto'
    name = fields.Char('Nombre', required=True)
    cia = fields.Many2One(
        'corseg.cia', 'Compania de Seguros', required=True)
    ramo = fields.Many2One(
        'corseg.ramo', 'Ramo', required=True)
    comision_cia = fields.MultiValue(fields.Many2One(
        'corseg.comision',
        'Comision Cia'))
    comision_vendedor = fields.MultiValue(fields.Many2One(
        'corseg.comision.vendedor',
        'Comision Vendedor'))
    comision_vendedor_defecto = fields.MultiValue(fields.Many2One(
        'corseg.comision',
        'Comision Vendedor por Defecto'))
    comisiones = fields.One2Many(
        'corseg.comisiones.cia.producto', 'cia_producto', 'Comisiones')
    polizas = fields.One2Many('corseg.poliza',
        'cia_producto', 'Polizas', readonly=True)
    es_colectiva = fields.Boolean('Colectiva')
    description = fields.Text('Descripcion', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True

    @classmethod
    def multivalue_model(cls, field):
        pool = Pool()
        if field in {'comision_cia', 'comision_vendedor',
                'comision_vendedor_defecto'}:
            return pool.get('corseg.comisiones.cia.producto')
        return super(CiaProducto, cls).multivalue_model(field)

    def get_comision_vendedor(self, poliza, vendedor, monto):
        result = Decimal('0.0')
        if not monto:
            return result

        if not self.comision_vendedor and \
                not self.comision_vendedor_defecto:
            return result

        if self.comision_vendedor:
            for linea in self.comision_vendedor.lineas:
                if linea.vendedor == vendedor:
                    return self._get_comision(poliza, linea.comision, monto)
        else:
            return self._get_comision(poliza, self.comision_vendedor_defecto, monto)

    def get_comision_cia(self, poliza, monto):
        result = Decimal('0.0')
        if not monto:
            return result

        if not self.comision_cia:
            return result

        return self._get_comision(poliza, self.comision_cia, monto)

    def _get_comision(self, poliza, comision, monto):
        last_linea = None
        for linea in comision:
            if linea.renovacion == poliza.renovacion:
                result = self._get_comision_linea(poliza, linea)
                break
            elif linea.renovacion > poliza.renovacion:
                if last_linea.tipo_comision.r_renovacion:
                    result = self._get_comision_linea(poliza, last_linea)
                break
            last_linea = linea
        return result

    def _get_comision_linea(self, poliza, linea):
        Pago = Pool().get('corseg.poliza.pago')
        result = Decimal('0.0')

        pagos = Pago.search([
                ('poliza', '=', poliza.id),
                ('renovacion', '=', poliza.renovacion)
            ])

        if not linea.tipo_comision.re_cuota and \
                pagos:
            return result

        if linea.tipo_comision.tipo == 'fijo':
            result = linea.tipo_comision.monto
        else:
            result = monto * (linea.tipo_comision.monto / 100)

        return result


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


class OrigenPoliza(ModelSQL, ModelView):
    'Origen Poliza'
    __name__ = 'corseg.poliza.origen'
    name = fields.Char('Nombre', required=True)
    notas = fields.Text('Notas', size=None)
    active = fields.Boolean('Activo')

    @staticmethod
    def default_active():
        return True


class ComentarioPoliza(ModelSQL, ModelView):
    'Comentarios sobre la Poliza'
    __name__ = 'corseg.poliza.comentario'
    poliza = fields.Many2One(
        'corseg.poliza', 'Poliza', required=True)
    fecha = fields.Date('Fecha', required=True)
    comentario = fields.Text('Comentario', size=None)
    made_by = fields.Many2One('res.user', 'Creado por',
        readonly=True)

    @classmethod
    def __setup__(cls):
        super(ComentarioPoliza, cls).__setup__()
        cls._order = [
                ('fecha', 'DESC'),
                ('id', 'DESC'),
            ]

    @staticmethod
    def default_fecha():
        pool = Pool()
        Date = pool.get('ir.date')
        return Date.today()

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if values.get('made_by') is None:
                values['made_by'] = Transaction().user
        comentarios = super(ComentarioPoliza, cls).create(vlist)
        return comentarios


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
    currency = fields.Many2One('currency.currency',
        'Moneda', required=False, # TODO required=True
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
    origen = fields.Many2One('corseg.poliza.origen', 'Origen')
    contratante = fields.Many2One('party.party', 'Contratante', readonly=True)
    f_emision = fields.Date('Emitida el',  readonly=True)
    f_desde = fields.Date('Desde',  readonly=True)
    f_hasta = fields.Date('Hasta',  readonly=True)
    renovacion = fields.Integer('Renovacion', readonly=True)
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
    comision_cia = fields.One2Many('corseg.comision.poliza.cia',
        'parent', 'Comision Cia', readonly=True)
    comision_vendedor = fields.One2Many('corseg.comision.poliza.vendedor',
        'parent', 'Comision Vendedor', readonly=True)
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
    state = fields.Selection([
            ('new', 'Nuevo'),
            ('vigente', 'Vigente'),
            ('cancelada', 'Cancelada'),
        ],
        'Estado', readonly=True, required=True)

    # TODO documentos

    @classmethod
    def __setup__(cls):
        super(Poliza, cls).__setup__()
        t = cls.__table__()
        cls._sql_constraints += [
            ('cia_product_numero_uniq', 
                Unique(t, t.cia_producto, t.numero),
                'El numero de poliza ya existe para este producto'),
        ]

        cls._error_messages.update({
            'comision_renovacion_cero': ('El primer registro de la tabla de '
                'comisiones dede ser para la renovacion zero. Poliza: "%s".'),
            'comision_renovacion_menor': ('El valor de la renovacion del '
                'registro de la tabla de comisiones debe ser mayor que '
                'el anterior. Poliza: "%s".'),
        })

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

    @fields.depends('cia', 'cia_producto', 'ramo', 'vendedor',
        'comision_cia', 'comision_vendedor')
    def on_change_cia_producto(self):
        self.ramo = None
        self.vendedor = None
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
        res = Decimal('0.0')
        if self.pagos:
            for pago in self.pagos:
                if pago.state not in \
                        ['borrador', 'procesado', 'sustituido']:
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
