#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, If, Not, In, Bool
from decimal import Decimal
from .tools import auditoria_field, get_current_date, set_auditoria

__all__ = ['FormaPago', 'FrecuenciaPago', 'Pago']


_STATES={
        'readonly': Not(In(Eval('state'), ['borrador',])),
    }

_DEPENDS=['state']


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


class Pago(Workflow, ModelSQL, ModelView):
    'Pago a Poliza'
    __name__ = 'corseg.poliza.pago'
    company = fields.Many2One('company.company', 'Company', required=False, # TODO required=True
        states={
            'readonly': True,
            },
        domain=[ #TODO descomentar despues de realizar la migracion
#            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
#                Eval('context', {}).get('company', -1)),
            ], select=True)
    number = fields.Char('Numero', size=None, readonly=True, select=True)
    currency = fields.Many2One('currency.currency',
        'Moneda', required=False, # TODO required=True
        readonly=True)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'get_currency_digits')
    poliza = fields.Many2One('corseg.poliza', 'Poliza', required=True,
        domain=[
            #('company', '=', Eval('company')), TODO descomentar despues de la migracion
            If(
                In(Eval('state'), ['confirmado']),
                [('state', '!=', '')],
                [('state', '!=', 'finalizada')]
            )
        ],
        states=_STATES, depends=['company', 'state'])
    cia = fields.Function(
        fields.Many2One('corseg.cia', 'Compania de Seguros'),
        'get_cia', searcher='search_cia')
    renovacion = fields.Integer('Renovacion', readonly=True)
    fecha = fields.Date('Fecha', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador', 'procesado'])),
        }, depends=['state'])
    referencia = fields.Char('Referencia',
        states={
            'readonly': Not(In(Eval('state'), ['borrador', 'procesado'])),
        }, depends=['state'])
    monto = fields.Numeric('Monto', required=True,
        digits=(16, Eval('currency_digits', 2)),
        states=_STATES, depends=['currency_digits'])
    vendedor = fields.Many2One('corseg.vendedor',
        'Vendedor', required=True,
        states=_STATES, depends=_DEPENDS)
    comision_cia = fields.Numeric('Comision Cia',
        digits=(16, Eval('currency_digits', 2)),
        required=True, states=_STATES,
        depends=['currency_digits'])
    comision_cia_sugerida = fields.Numeric(
        'Comision Cia Sugerida', readonly=True,
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'])
    comision_cia_ajuste = fields.Numeric(
        'Comision Cia Ajuste', readonly=True,
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'])
    comision_cia_liq = fields.Function(
        fields.Numeric('Comision Cia a Liquidar',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'on_change_with_comision_cia_liq')
    comision_vendedor = fields.Numeric('Comision vendedor',
        digits=(16, Eval('currency_digits', 2)),
        required=True, states=_STATES,
        depends=['currency_digits'])
    comision_vendedor_sugerida = fields.Numeric(
        'Comision Vendedor Sugerida', readonly=True,
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'])
    comision_vendedor_ajuste = fields.Numeric(
        'Comision Vendedor Ajuste', readonly=True,
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'])
    comision_vendedor_liq = fields.Function(
        fields.Numeric('Comision Vendedor a Liquidar',
            digits=(16, Eval('currency_digits', 2)),
            depends=['currency_digits']),
        'on_change_with_comision_vendedor_liq')
    ajustes_comision_cia = fields.One2Many(
        'corseg.comision.ajuste.cia',
        'pago', 'Ajustes Comision Cia', readonly=True)
    ajustes_comision_vendedor = fields.One2Many(
        'corseg.comision.ajuste.vendedor',
        'pago', 'Ajustes Comision Vendedor', readonly=True)
    comentario = fields.Text('Comentarios', size=None,
        states={
            'readonly': Not(In(Eval('state'), ['borrador', 'procesado'])),
        }, depends=['state'])
    sustituir = fields.Boolean('Sustituir',
        states=_STATES, depends=['state'])
    pago_sustituir = fields.Many2One(
        'corseg.poliza.pago', 'Sustituye a',
        domain=[
            ('company', '=', Eval('company')),
            If(
                In(Eval('state'), ['borrador', 'procesado']),
                ('state', '=', 'confirmado'),
                ('state', '!=', '')
            ),
        ],
        states={
            'invisible': Not(Bool(Eval('sustituir'))),
            'readonly': Not(In(Eval('state'), ['borrador',])),
            'required': Bool(Eval('sustituir')),
        }, depends=['company', 'state', 'sustituir'])
    sustituido_por = fields.Many2One(
        'corseg.poliza.pago', 'Sustituido por', readonly=True,
        states={
            'invisible': Not(In(Eval('state'), ['sustituido',])),
        }, depends=['state'])
    liq_cia = fields.Many2One('corseg.liquidacion.cia',
        'Liq. Cia', readonly=True)
    liq_vendedor = fields.Many2One('corseg.liquidacion.vendedor',
        'Liq. Vendedor', readonly=True)
    state = fields.Selection([
            ('borrador', 'Borrador'),
            ('procesado', 'Procesado'),
            ('confirmado', 'Confirmado'),
            ('cancelado', 'Cancelado'),
            ('sustituido', 'Sustituido'),
            ('liq_cia', 'Liquidado por Cia'),
            ('liq_vendedor', 'Liquidado al Vendedor'),
        ], 'Estado', required=True, readonly=True)
    made_by = auditoria_field('user', 'Creado por')
    made_date = auditoria_field('date', 'fecha')
    processed_by = auditoria_field('user', 'Procesado por')
    processed_date = auditoria_field('date', 'fecha')
    confirmed_by = auditoria_field('user', 'Confirmado por')
    confirmed_date = auditoria_field('date', 'fecha')
    canceled_by = auditoria_field('user', 'Cancelado por')
    canceled_date = auditoria_field('date', 'fecha')

    @classmethod
    def __setup__(cls):
        super(Pago, cls).__setup__()
        cls._order = [
                ('number', 'DESC'),
                ('fecha', 'DESC'),
            ]
        cls._error_messages.update({
                'delete_cancel': ('El Pago "%s" debe ser '
                    'cancelado antes de eliminarse.'),
                'pago_confirmado': ('El Pago a sustiruir en el Pago "%s" '
                    'debe tener un estado de "Confirmado".'),
                })
        cls._transitions |= set(
            (
                ('borrador', 'procesado'),
                ('procesado', 'confirmado'),
                ('procesado', 'cancelado'),
                ('cancelado', 'borrador'),
            )
        )
        cls._buttons.update({
            'cancelar': {
                'invisible': Not(In(Eval('state'), ['procesado'])),
                },
            'procesar': {
                'invisible': ~Eval('state').in_(['borrador']),
                },
            'confirmar': {
                'invisible': ~Eval('state').in_(['procesado']),
                },
            'borrador': {
                'invisible': ~Eval('state').in_(['cancelado']),
                'icon': If(Eval('state') == 'cancelado',
                    'tryton-clear', 'tryton-go-previous'),
                },
            })

    @staticmethod
    def default_company():
        return Transaction().context.get('company')

    @staticmethod
    def default_state():
        return 'borrador'

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

    @staticmethod
    def default_comision_cia():
        return Decimal('0.0')

    @staticmethod
    def default_comision_cia_sugerida():
        return Decimal('0.0')

    @staticmethod
    def default_comision_cia_ajuste():
        return Decimal('0.0')

    @staticmethod
    def default_comision_cia_liq():
        return Decimal('0.0')

    @staticmethod
    def default_comision_vendedor():
        return Decimal('0.0')

    @staticmethod
    def default_comision_vendedor_sugerida():
        return Decimal('0.0')

    @staticmethod
    def default_comision_vendedor_ajuste():
        return Decimal('0.0')

    @staticmethod
    def default_comision_vendedor_liq():
        return Decimal('0.0')

    @fields.depends('monto', 'comision_cia', 'comision_cia_ajuste')
    def on_change_with_comision_cia_liq(self, name=None):
        return self.comision_cia + self.comision_cia_ajuste

    @fields.depends('monto', 'comision_vendedor', 'comision_vendedor_ajuste')
    def on_change_with_comision_vendedor_liq(self, name=None):
        return self.comision_vendedor + self.comision_vendedor_ajuste

    @fields.depends('poliza', 'vendedor', 'monto',
            'comision_cia', 'comision_vendedor',
            'comision_cia_sugerida', 'comision_vendedor_sugerida',
            'comision_cia_liq', 'comision_vendedor_liq')
    def on_change_monto(self):
        Comision = Pool().get('corseg.comision')
        self.comision_cia = Decimal('0.0')
        self.comision_vendedor = Decimal('0.0')
        self.comision_cia_sugerida = Decimal('0.0')
        self.comision_vendedor_sugerida = Decimal('0.0')
        self.comision_cia_liq = Decimal('0.0')
        self.comision_vendedor_liq = Decimal('0.0')
        if self.monto:
            if self.poliza:
                if self.poliza.comision_cia:
                    self.comision_cia = \
                        Comision.get_comision(
                            self.poliza,
                            self.poliza.comision_cia,
                            self.monto)
                elif self.poliza.cia_producto.comision_cia:
                    self.comision_cia = \
                        Comision.get_comision(
                            self.poliza,
                            self.poliza.cia_producto.comision_cia.lineas,
                            self.monto)

            if self.poliza and self.vendedor:
                if self.poliza.comision_vendedor:
                    self.comision_vendedor = \
                        Comision.get_comision(
                            self.poliza,
                            self.poliza.comision_vendedor,
                            self.monto)

                elif self.poliza.cia_producto.comision_vendedor:
                    found = False
                    for line in self.poliza.cia_producto.comision_vendedor:
                        if line.vendedor.id == self.vendedor.id:
                            self.comision_vendedor = \
                                Comision.get_comision(
                                    self.poliza,
                                    line.comision.lineas,
                                    self.monto)
                            found = True
                            break
                    if not found and \
                            self.poliza.cia_producto.comision_vendedor_defecto:
                        self.comision_vendedor = Comision.get_comision(
                            self.poliza,
                            self.poliza.cia_producto.comision_vendedor_defecto.lineas,
                            self.monto)

                elif self.poliza.cia_producto.comision_vendedor_defecto:
                    self.comision_vendedor = Comision.get_comision(
                        self.poliza,
                        self.poliza.cia_producto.comision_vendedor_defecto.lineas,
                        self.monto)

            self.comision_cia_sugerida = self.comision_cia
            self.comision_vendedor_sugerida = self.comision_vendedor

    @fields.depends('poliza', 'cia', 'currency_digits',
            'vendedor', 'renovacion', 'monto',
            'comision_cia', 'comision_vendedor',
            'comision_cia_sugerida', 'comision_vendedor_sugerida',
            'comision_cia_liq', 'comision_vendedor_liq')
    def on_change_poliza(self):
        self.cia = None
        self.vendedor = None
        self.currency_digits = 2
        self.renovacion = None
        if self.poliza:
            self.cia = self.poliza.cia
            self.currency_digits = \
                self.poliza.currency_digits
            self.vendedor = self.poliza.vendedor
            self.renovacion = self.poliza.renovacion
        self.on_change_monto()

    @fields.depends('poliza', 'vendedor', 'monto',
            'comision_cia', 'comision_vendedor',
            'comision_cia_sugerida', 'comision_vendedor_sugerida',
            'comision_cia_liq', 'comision_vendedor_liq')
    def on_change_vendedor(self):
        self.on_change_monto()

    def get_rec_name(self, name):
        if self.number:
            return self.number
        else:
            return self.id

    def get_cia(self, name):
        if self.poliza:
            return self.poliza.cia.id

    def get_currency_digits(self, name=None):
        if self.poliza:
            self.poliza.currency_digits
        return 2

    @classmethod
    def search_cia(cls, name, clause):
        return [('poliza.cia',) + tuple(clause[1:])]

    @classmethod
    def set_number(cls, pagos):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('corseg.configuration')
        config = Config(1)
        for pago in pagos:
            if pago.number:
                continue
            pago.number = Sequence.get_id(config.pago_seq.id)
        cls.save(pagos)

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if values.get('made_by') is None:
                values['made_by'] = Transaction().user
                values['made_date'] = get_current_date()
        pagos = super(Pago, cls).create(vlist)
        return pagos

    @classmethod
    def delete(cls, pagos):
        for pago in pagos:
            if pago.state not in ['borrador', 'cancelado']:
                cls.raise_user_error('delete_cancel', (pago.rec_name,))
        super(Pago, cls).delete(pagos)

    @classmethod
    @ModelView.button
    @Workflow.transition('borrador')
    def borrador(cls, movs):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('procesado')
    def procesar(cls, pagos):
        for pago in pagos:
            set_auditoria(pago, 'processed')
            pago.currency = pago.company.currency #TODO borrar despues de migrar
            pago.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmado')
    def confirmar(cls, pagos):
        for pago in pagos:
            if pago.sustituir:
                if pago.pago_sustituir.state != 'confirmado':
                    cls.raise_user_error(
                        'pago_confirmado', (pago.rec_name,))
                pago.pago_sustituir.state = 'sustituido'
                pago.pago_sustituir.sustituido_por = pago
                pago.pago_sustituir.save()
            set_auditoria(pago, 'confirmed')
            pago.save()
        cls.set_number(pagos)

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, pagos):
        for pago in pagos:
            set_auditoria(pago, 'canceled')
            pago.save()
