#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, If, Not, In
from .tools import auditoria_field, get_current_date, set_auditoria

__all__ = [
        'Pago',
    ]


_STATES={
        'readonly': Not(In(Eval('state'), ['borrador',])),
    }

_DEPENDS=['state']


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
    # TODO numero
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
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['company', 'state'])
    cia = fields.Function(
        fields.Many2One('corseg.cia', 'Compania de Seguros'),
        'get_cia', searcher='search_cia')
    fecha = fields.Date('Fecha', required=True,
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
        }, depends=['state'])
    referencia = fields.Char('Referencia',
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
        }, depends=['state'])
    monto = fields.Numeric('Monto',
        digits=(16, Eval('currency_digits', 2)),
        required=True, states=_STATES, depends=['currency_digits'])
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=_DEPENDS)
    comision_cia = fields.Numeric('Comision Cia',
        digits=(16, Eval('currency_digits', 2)),
        required=True, states=_STATES, depends=['currency_digits'])
    comision_vendedor = fields.Numeric('Comision vendedor',
        digits=(16, Eval('currency_digits', 2)),
        required=True, states=_STATES, depends=['currency_digits'])
    comentario = fields.Text('Comentarios', size=None,
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
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
        cls._order[0] = ('fecha', 'DESC')
        cls._error_messages.update({
                'delete_cancel': ('El Pago "%s" debe ser '
                    'cancelado antes de eliminarse.'),
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
    def default_currency_digits():
        return 2

    @fields.depends('poliza', 'cia', 'currency_digits')
    def on_change_poliza(self):
        self.cia = None
        self.currency_digits = 2
        if self.poliza:
            self.cia = self.poliza.cia
            self.currency_digits = \
                self.poliza.currency_digits
            # TODO rellenar los valores por defecto de esta poliza:
            #      comision_cia, vendedor y tabla de comisiones por defecto

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
            pago.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmado')
    def confirmar(cls, pagos):
        for pago in pagos:
            set_auditoria(pago, 'confirmed')
            pago.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, pagos):
        # TODO cambiar el state de la poliza,
        # si es su primer movimiento debe asignarse 'new'
        for pago in pagos:
            set_auditoria(pago, 'canceled')
            pago.save()
