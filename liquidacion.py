#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, Bool, If, Not, In
from decimal import Decimal
from .tools import auditoria_field, get_current_date, set_auditoria

__all__ = [
        'LiquidacionCia',
        'LiquidacionVendedor',
        'LiquidacionPagoCia',
        'LiquidacionPagoVendedor',
    ]


_STATE = [
        ('borrador', 'Borrador'),
        ('procesado', 'Procesado'),
        ('confirmado', 'Confirmado'),
        ('cancelado', 'Cancelado'),
    ]


class LiquidacionBase(Workflow, ModelSQL, ModelView):
    company = fields.Many2One('company.company',
        'Company', required=True,
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    number = fields.Char('Numero', size=None, readonly=True, select=True)
    currency = fields.Many2One('currency.currency',
        'Moneda', required=False, # TODO required=True
        readonly=True)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'get_currency_digits')
    fecha = fields.Date('Fecha', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
    referencia = fields.Char('Referencia',
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
        }, depends=['state'])
    comentario = fields.Text('Comentarios', size=None,
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
        }, depends=['state'])
    state = fields.Selection(_STATE, 'Estado',
        required=True, readonly=True)
    total = fields.Function(fields.Numeric('Total',
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits']), 'get_total')
    total_cache = fields.Numeric('Total',
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits'])
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
        super(LiquidacionBase, cls).__setup__()
        cls._order = [
                ('number', 'DESC'),
                ('fecha', 'DESC'),
            ]
        cls._error_messages.update({
                'delete_cancel': ('La Liquidacion "%s" debe estar '
                    'cancelada antes de eliminarse.'),
                'ajuste_state': ('El Estado del Ajuste "%s" '
                    'es invalido.'),
                'pago_confirmado': ('El Estado del Pago "%s" '
                    'debe ser "Confirmado".'),
                'pago_liq_cia': ('El Estado del Pago "%s" '
                    'debe ser "Liquidado por la Cia".'),
                'diff_no_cero': ('La diferencia debe ser igual a cero.'),
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

    def get_rec_name(self, name):
        if self.number:
            return self.number
        else:
            return self.id

    def _get_total(self, pagos, ente):
        total = Decimal('0.0')
        if pagos:
            for pago in pagos:
                total += getattr(pago, 'comision_' + ente + '_liq')
        return total

    def get_currency_digits(self, name=None):
        if self.company:
            self.company.currency.digits
        return 2

    @classmethod
    def set_number(cls, liqs, seq_name=None):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('corseg.configuration')
        config = Config(1)
        for liq in liqs:
            if liq.number:
                continue
            seq = getattr(config, seq_name)
            liq.number = Sequence.get_id(seq.id)
        cls.save(liqs)

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if values.get('made_by') is None:
                values['made_by'] = Transaction().user
                values['made_date'] = get_current_date()
        liqs = super(LiquidacionBase, cls).create(vlist)
        return liqs

    @classmethod
    def delete(cls, liqs):
        for liq in liqs:
            if liq.state not in ['borrador', 'cancelado']:
                cls.raise_user_error('delete_cancel', (liq.rec_name,))
        super(LiquidacionBase, cls).delete(liqs)

    @classmethod
    def store_cache(cls, liqs):
        for liq in liqs:
            cls.write([liq], {
                    'total_cache': liq.total,
                    })


class LiquidacionCia(LiquidacionBase):
    'Liquidacion Comisiones Cia de Seguros'
    __name__ = 'corseg.liquidacion.cia'
    cia = fields.Many2One(
        'corseg.cia', 'Compania de Seguros', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
    monto_pagado = fields.Numeric('Monto Pagado', #required=True, TODO Descomentar despues de migrar
        digits=(16, Eval('currency_digits', 2)),
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state', 'currency_digits'])
    diff = fields.Function(fields.Numeric('Diferencia',
        digits=(16, Eval('currency_digits', 2)),
        depends=['currency_digits']), 'on_change_with_diff')
    pagos = fields.Many2Many(
        'poliza.pagos-liquidacion.cia',
        'liquidacion', 'pago', 'Pagos',
        domain=[
            ('company', '=', Eval('company')),
            ('currency', '=', Eval('currency')),
            ('cia', '=', Eval('cia')),
            If(
                In(Eval('state'), ['borrador', 'procesado']),
                ('state', '=', 'confirmado'),
                ('state', '!=', '')
            )
        ],
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
            'invisible': Not(Bool(Eval('cia'))),
        }, depends=['company', 'currency', 'cia', 'state'])

    @fields.depends('pagos')
    def on_change_pagos(self):
        self.total = self.get_total()

    def get_total(self, name=None):
        return super(LiquidacionCia, self)._get_total(
            self.pagos, 'cia')

    @fields.depends('pagos', 'monto_pagado', 'total')
    def on_change_with_diff(self, name=None):
        res = Decimal('0.0')
        if self.monto_pagado:
            res = self.monto_pagado
            if self.total:
                res -= self.total
        return res

    @classmethod
    def _compensar_ajuste(cls, factor, first, ajuste):
        Compensacion = Pool().get(
            'corseg.comision.ajuste.cia.compensacion')

        saldo = first.monto_pendiente + ajuste.monto_pendiente
        compensar_first = False
        compensar_ajuste = False
        if saldo == 0:
            res = ajuste.monto_pendiente
            compensar_first = True
            compensar_ajuste = True
        elif (factor == 1 and saldo > 0) or \
                (factor == -1 and saldo < 0):
            res = ajuste.monto_pendiente
            compensar_ajuste = True
        else:
            res = -first.monto_pendiente
            compensar_first = True

        compensacion = Compensacion(
                ajuste=first,
                ajuste_compensa=ajuste,
                monto = res
            )
        compensacion.save()

        if compensar_first:
            first.state = 'compensado'
            first.save()
        if compensar_ajuste:
            ajuste.state = 'compensado'
            ajuste.save()

    @classmethod
    def _update_ajustes(cls, pago):
        pool = Pool()
        Ajuste = pool.get('corseg.comision.ajuste.cia')

        for ajuste in pago.ajustes_comision_cia:
            if ajuste.state != 'procesado':
                cls.raise_user_error(
                    'ajuste_state', (ajuste.rec_name,))
            ajuste.state = 'pendiente'
            ajuste.save()

        requery = True
        while requery:
            ajs = Ajuste.search([
                    ('pago.poliza', '=', pago.poliza.id),
                    ('state', '=', 'pendiente'),
                ], order=[('number', 'ASC')])

            requery = False
            first = None
            factor = None
            for ajuste in ajs:
                if first is None:
                    first = ajuste
                    if first.monto_pendiente > 0:
                        factor = 1
                    else:
                        factor = -1
                else:
                    if (factor == 1 and ajuste.monto_pendiente < 0) or \
                            (factor == -1 and ajuste.monto_pendiente > 0):
                        cls._compensar_ajuste(factor, first, ajuste)
                        requery = True
                        break

    @classmethod
    def set_number(cls, liqs):
        super(LiquidacionCia, cls).set_number(
            liqs, seq_name='liq_cia_seq')

    @classmethod
    @ModelView.button
    @Workflow.transition('borrador')
    def borrador(cls, liqs):
        for liq in liqs:
            for pago in liq.pagos:
                for ajuste in pago.ajustes_comision_cia:
                    ajuste.state = 'borrador'
                    ajuste.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('procesado')
    def procesar(cls, liqs):
        for liq in liqs:
            if liq.diff != 0:
                cls.raise_user_error('diff_no_cero')
            for pago in liq.pagos:
                for ajuste in pago.ajustes_comision_cia:
                    if ajuste.state != 'borrador': 
                        cls.raise_user_error(
                            'ajuste_state', (ajuste.rec_name,))
                    ajuste.state = 'procesado'
                    ajuste.save()
            set_auditoria(liq, 'processed')
            liq.save()
        cls.store_cache(liqs)

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmado')
    def confirmar(cls, liqs):
        for liq in liqs:
            if liq.diff != 0:
                cls.raise_user_error('diff_no_cero')
            for pago in liq.pagos:
                if pago.state != 'confirmado':
                    cls.raise_user_error(
                        'pago_confirmado', (pago.rec_name,))

                cls._update_ajustes(pago)

                pago.liq_cia = liq
                pago.state = 'liq_cia'
                pago.save()
            set_auditoria(liq, 'confirmed')
            liq.save()

        cls.set_number(liqs)
        cls.store_cache(liqs)

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, liqs):
        for liq in liqs:
            for pago in liq.pagos:
                for ajuste in pago.ajustes_comision_cia:
                    ajuste.state = 'cancelado'
                    ajuste.save()
            set_auditoria(liq, 'canceled')
            liq.save()
        cls.store_cache(liqs)


class LiquidacionVendedor(LiquidacionBase):
    'Liquidacion Comisiones Vendedor'
    __name__ = 'corseg.liquidacion.vendedor'
    vendedor = fields.Many2One('corseg.vendedor',
        'Vendedor', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
    pagos = fields.Many2Many(
        'poliza.pagos-liquidacion.vendedor',
        'liquidacion', 'pago', 'Pagos',
        domain=[
            ('company', '=', Eval('company')),
            ('currency', '=', Eval('currency')),
            ('vendedor', '=', Eval('vendedor')),
            If(
                In(Eval('state'), ['borrador', 'procesado']),
                ('state', '=', 'liq_cia'),
                ('state', '!=', '')
            )
        ],
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
            'invisible': Not(Bool(Eval('vendedor'))),
        }, depends=['company', 'currency', 'vendedor', 'state'])

    @fields.depends('pagos')
    def on_change_pagos(self):
        self.total = self.get_total()

    def get_total(self, name=None):
        return super(LiquidacionVendedor, self)._get_total(
            self.pagos, 'vendedor')

    @classmethod
    def set_number(cls, liqs):
        super(LiquidacionVendedor, cls).set_number(
            liqs, seq_name='liq_vendedor_seq')

    @classmethod
    @ModelView.button
    @Workflow.transition('borrador')
    def borrador(cls, liqs):
        for liq in liqs:
            for pago in liq.pagos:
                for ajuste in pago.ajustes_comision_vendedor:
                    ajuste.state = 'borrador'
                    ajuste.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('procesado')
    def procesar(cls, liqs):
        for liq in liqs:
            for pago in liq.pagos:
                for ajuste in pago.ajustes_comision_vendedor:
                    if ajuste.state != 'borrador': 
                        cls.raise_user_error(
                            'ajuste_state', (ajuste.rec_name,))
                    ajuste.state = 'procesado'
                    ajuste.save()
            set_auditoria(liq, 'processed')
            liq.save()
        cls.store_cache(liqs)

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmado')
    def confirmar(cls, liqs):
        for liq in liqs:
            for pago in liq.pagos:
                for ajuste in pago.ajustes_comision_vendedor:
                    if ajuste.state != 'procesado': 
                        cls.raise_user_error(
                            'ajuste_state', (ajuste.rec_name,))
                    ajuste.state = 'confirmado'
                    ajuste.save()
                if pago.state != 'liq_cia':
                    cls.raise_user_error(
                        'pago_liq_cia', (pago.rec_name,))
                pago.liq_vendedor = liq
                pago.state = 'liq_vendedor'
                pago.save()
            set_auditoria(liq, 'confirmed')
            liq.save()
        cls.set_number(liqs)
        cls.store_cache(liqs)
        # TODO crear el account_move

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, liqs):
        for liq in liqs:
            for pago in liq.pagos:
                for ajuste in pago.ajustes_comision_vendedor:
                    ajuste.state = 'cancelado'
                    ajuste.save()
            set_auditoria(liq, 'canceled')
            liq.save()
        cls.store_cache(liqs)


class LiquidacionPagoCia(ModelSQL):
    'Pago - Liquidacion Cia'
    __name__ = 'poliza.pagos-liquidacion.cia'
    pago = fields.Many2One('corseg.poliza.pago',
        'Pago', ondelete='CASCADE', select=True, required=True)
    liquidacion = fields.Many2One('corseg.liquidacion.cia',
        'Liquidacion', ondelete='CASCADE', select=True, required=True)


class LiquidacionPagoVendedor(ModelSQL):
    'Pago - Liquidacion Vendedor'
    __name__ = 'poliza.pagos-liquidacion.vendedor'
    pago = fields.Many2One('corseg.poliza.pago',
        'Pago', ondelete='CASCADE', select=True, required=True)
    liquidacion = fields.Many2One('corseg.liquidacion.vendedor',
        'Liquidacion', ondelete='CASCADE', select=True, required=True)
