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
        'PolizaDocumento',
        'Poliza',
        'Renovacion',
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
        'corseg.cia', 'Cia de Seguros', required=True,
        states={ 
            'readonly': Bool(Eval('polizas')),
        }, depends=['polizas'])
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


class GrupoPoliza(ModelSQL, ModelView):
    'Grupo de Polizas'
    __name__ = 'corseg.poliza.grupo'
    company = fields.Many2One('company.company', 'Empresa', required=True,
        states={
            'readonly': True,
        },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
        ], select=True)
    name = fields.Char('Nombre', required=True)
    parent = fields.Many2One('corseg.poliza.grupo', 'Padre', select=True)
    childs = fields.One2Many('corseg.poliza.grupo',
        'parent', 'Hijos', readonly=True)
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


class PolizaDocumento(ModelSQL, ModelView):
    'Documento Poliza'
    __name__ = 'corseg.poliza.documento'

    poliza = fields.Many2One('corseg.poliza', 'Poliza',
        ondelete='CASCADE', select=True, required=True)
    name = fields.Char('Nombre', required=True)
    comentario = fields.Text('Comentario', size=None)
    documento = fields.Binary('Documento', file_id='doc_id',
        required=True)
    doc_id = fields.Char('Doc id',
            states={'invisible': True}
        )


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
    currency = fields.Many2One('currency.currency',
        'Moneda', required=True,
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
        'Cia de Seguros', required=True,
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
    ramo = fields.Function(fields.Many2One(
        'corseg.ramo', 'Ramo'),
        'get_ramo',
        searcher='search_ramo')
    numero = fields.Char('Numero de Poliza', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['new'])),
            },
        depends=['state'])
    origen = fields.Many2One('corseg.poliza.origen', 'Origen')
    contratante = fields.Many2One('party.party', 'Contratante', readonly=True)
    renovacion = fields.Function(fields.Integer('Renovacion actual'),
        'get_renovacion_dato')
    f_emision = fields.Function(fields.Date('Emitida el'),
        'get_renovacion_dato')
    f_desde = fields.Function(fields.Date('Desde:'),
        'get_renovacion_dato')
    f_hasta = fields.Function(fields.Date('Hasta:'),
        'get_renovacion_dato')
    suma_asegurada = fields.Function(fields.Numeric('Suma Asegurada',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_renovacion_dato')
    prima = fields.Function(fields.Numeric('Prima',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_renovacion_dato')
    total = fields.Function(fields.Numeric('Total',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_renovacion_dato')
    renovaciones = fields.One2Many('corseg.poliza.renovacion',
        'poliza', 'Renovaciones', readonly=True)
    vendedor = fields.Many2One('corseg.vendedor',
        'Vendedor', readonly=True)
    notas = fields.Text('Notas', size=None)
    forma_pago = fields.Many2One('corseg.forma_pago',
        'Forma pago', readonly=True)
    frecuencia_pago = fields.Many2One('corseg.frecuencia_pago',
        'Frecuencia pago',  readonly=True)
    no_cuotas = fields.Integer('Cant. cuotas', readonly=True)
    cuota = fields.Function(fields.Numeric('Cuota',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_cuota')
    cuota_prima = fields.Function(fields.Numeric('Cuota Prima',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'get_cuota_prima')
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
        'poliza', 'Pagos', readonly=True,
        filter=[
            ('state', '!=', 'sustituido'),
        ],
        states={
            'invisible': Equal(Eval('state'), 'new'),
            },
        depends=['state'])
    reclamos = fields.One2Many('corseg.poliza.reclamo',
        'poliza', 'Reclamos', readonly=True,
        states={
            'invisible': Equal(Eval('state'), 'new'),
            },
        depends=['state'])
    comentarios = fields.One2Many('corseg.poliza.comentario',
        'poliza', 'Comentarios')
    documentos = fields.One2Many('corseg.poliza.documento',
        'poliza', 'Documentos')
    vencida = fields.Function(
            fields.Boolean('Vencida'),
            'get_vencida')
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

    def get_vencida(self, name):
        pool = Pool()
        Date = pool.get('ir.date')
        if self.state != 'vigente':
            return False
        if not self.f_hasta:
            return False
        if self.f_hasta < Date.today():
            return True
        return False

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
            self.ramo = self.cia_producto.ramo

    @fields.depends('currency')
    def on_change_with_currency_digits(self, name=None):
        if self.currency:
            return self.currency.digits
        return 2

    def get_renovacion_dato(self, name):
        if self.renovaciones:
            return getattr(self.renovaciones[0], name)

    def get_ramo(self, name):
        if self.cia_producto:
            return self.cia_producto.ramo.id

    def get_monto_pago(self, name):
        Renovacion = Pool().get('corseg.poliza.renovacion')

        # Obtenemos el saldo de la renovacion anterior,
        # El cual deberia ser cero, sin embargo hay casos
        # donde se paga de mas, por lo que el saldo es negativo
        res = -Renovacion.get_saldo_poliza_renovacion(
            self, None if self.renovacion is None else self.renovacion - 1)

        if self.pagos:
            for pago in self.pagos:
                if pago.renovacion != self.renovacion:
                    continue
                if pago.state not in pago.valid_states():
                    res += pago.monto
        return res

    def get_cuota(self, name):
        if self.total:
            exp = Decimal(str(10.0 ** -self.currency_digits))
            return (self.total / self.no_cuotas).quantize(exp)

    def get_cuota_prima(self, name):
        if self.prima:
            exp = Decimal(str(10.0 ** -self.currency_digits))
            return (self.prima / self.no_cuotas).quantize(exp)

    def get_saldo(self, name):
        res = Decimal('0.0')
        if self.total:
            res = self.total - self.monto_pago
        return res

    @classmethod
    def search_ramo(cls, name, clause):
        return [('cia_producto.ramo',) + tuple(clause[1:])]

    @classmethod
    def write(cls, *args):
        super(Poliza, cls).write(*args)
        pool = Pool()
        Party = pool.get('party.party')
        actions = iter(args)
        args = []
        parties = []
        for polizas, values in zip(actions, actions):
            for poliza in polizas:
                if poliza.contratante:
                    parties.append(poliza.contratante)
        Party.set_is_contratante(parties)

    @classmethod
    def delete(cls, polizas):
        super(Poliza, cls).delete(polizas)
        pool = Pool()
        Party = pool.get('party.party')
        parties = []
        for poliza in polizas:
            if poliza.contratante:
                parties.append(poliza.contratante)
        Party.set_is_contratante(parties)


class Renovacion(ModelSQL, ModelView):
    'Poliza Renovacion'
    __name__ = 'corseg.poliza.renovacion'

    poliza = fields.Many2One('corseg.poliza',
        'Poliza', required=True)
    renovacion = fields.Integer('Renovacion', readonly=True)
    f_emision = fields.Date('Emitida el',  readonly=True)
    f_desde = fields.Date('Desde', readonly=True)
    f_hasta = fields.Date('Hasta', readonly=True)
    suma_asegurada = fields.Numeric('Suma Asegurada',
        digits=(16, Eval('_parent_currency_digits', 2)), readonly=True)
    prima = fields.Numeric('Prima',
        digits=(16, Eval('_parent_currency_digits', 2)), readonly=True)
    pagos = fields.Function(fields.Numeric('Pagos',
            digits=(16, Eval('_parent_currency_digits', 2))),
        'get_pagos')
    total = fields.Function(fields.Numeric('Total',
            digits=(16, Eval('_parent_currency_digits', 2))),
        'get_total')
    saldo = fields.Function(fields.Numeric('Saldo',
            digits=(16, Eval('_parent_currency_digits', 2))),
        'get_saldo')

    @classmethod
    def __setup__(cls):
        super(Renovacion, cls).__setup__()
        cls._order = [
                ('renovacion', 'DESC'),
            ]

        cls._error_messages.update({
            'fecha_emision_mayor': ('La fecha de emision de la poliza "%s" '
                'no puede ser mayor a la fecha de inicio de la vigencia. '
                'Renovacion: "%s".'),
            'fecha_hasta_menor': ('La fecha de finalizacion de la vigencia '
                'de la poliza "%s" no puede ser menor que la fecha de inicio '
                'de la misma. Renovacion: "%s".'),
            'dias_diff_emision': ('La fecha de emision tiene mas de "%s" dias '
                'de diferencia con respecto a la fecha de inicio de la vigencia '
                'de la poliza "%s". Renovacion: "%s".'),
            'dias_diff_vigencia': ('La diferencia entre el inicio y '
                'la finalizacion de la vigencia de la poliza "%s" es mayor '
                'a "%s" dias. Renovacion: "%s".'),
            'fecha_renovacion_desde_menor': ('La fecha de inicio de la vigencia '
                'de la poliza "%s" no debe ser menor a la fecha de finalizacion de '
                'la vigencia anterior. Renovacion: "%s".'),
        })

    def get_total(self, name):
        result = Decimal('0.0')
        if self.prima:
            result += self.prima
        return result

    def get_pagos(self, name):
        pool = Pool()
        Pago = pool.get('corseg.poliza.pago')
        result = Decimal('0.0')
        if self.poliza and self.prima is not None \
                and self.renovacion is not None:
            pagos = Pago.search([
                    ('poliza', '=', self.poliza.id),
                    ('renovacion', '=', self.renovacion),
                    ('state', 'not in', Pago.valid_states()),
                ])
            for pago in pagos:
                result += pago.monto
        return result

    def get_saldo(self, name):
        return self.total - self.pagos

    @classmethod
    def validate(cls, renovaciones):
        Renovacion = Pool().get('corseg.poliza.renovacion')
        dias_diff_emision = 30      # TODO debe estar en configuracion
        dias_diff_vigencia = 1100   # en el ramo?

        for reno in renovaciones:
            if reno.f_emision > reno.f_desde:
                cls.raise_user_error(
                    'fecha_emision_mayor',
                    (reno.poliza.rec_name, reno.renovacion))
            if reno.f_hasta < reno.f_desde:
                cls.raise_user_error(
                    'fecha_hasta_menor',
                    (reno.poliza.rec_name, reno.renovacion))
            if (reno.f_desde - reno.f_emision).days > dias_diff_emision:
                cls.raise_user_error(
                    'dias_diff_emision',
                    (dias_diff_emision, reno.poliza.rec_name, reno.renovacion))
            if (reno.f_hasta - reno.f_desde).days > dias_diff_vigencia:
                cls.raise_user_error(
                    'dias_diff_vigencia',
                    (reno.poliza.rec_name, dias_diff_vigencia, reno.renovacion))
            if reno.renovacion > 0:
                reno_anterior = Renovacion.search([
                        ('poliza', '=', reno.poliza.id),
                        ('renovacion', '=', reno.renovacion - 1),
                    ])[0]
                if reno.f_desde < reno_anterior.f_hasta:
                    cls.raise_user_error(
                        'fecha_renovacion_desde_menor',
                        (reno.poliza.rec_name, reno.renovacion))

    @classmethod
    def get_saldo_poliza_renovacion(cls, poliza, renovacion):
        pool = Pool()
        Renovacion = pool.get('corseg.poliza.renovacion')
        Pago = pool.get('corseg.poliza.pago')

        result = Decimal('0.0')

        if not poliza or renovacion is None or renovacion < 0:
            return result

        renovaciones = Renovacion.search([
                ('poliza', '=', poliza.id),
                ('renovacion', '<=', renovacion)
            ])

        for reno in renovaciones:
            result += reno.total
            pagos = Pago.search([
                    ('poliza', '=', poliza.id),
                    ('renovacion', '=', reno.renovacion),
                    ('state', 'not in', Pago.valid_states()),
                ])
            for pago in pagos:
                result -= pago.monto

        return result


class Vendedor(ModelSQL, ModelView):
    'Vendedor'
    __name__ = 'corseg.vendedor'
    party = fields.Many2One('party.party', 'Party', required=True,
            ondelete='CASCADE')
    alias = fields.Char('Alias')
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
