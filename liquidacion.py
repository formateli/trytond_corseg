#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, Bool, If, Not, In
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
        ('posted', 'Posteado'),
        ('cancelado', 'Cancelado'),
    ]


class LiquidacionCia(Workflow, ModelSQL, ModelView):
    'Liquidacion Comisiones Cia de Seguros'
    __name__ = 'corseg.liquidacion.cia'
    company = fields.Many2One('company.company', 'Company', required=False, # TODO required=True
        states={
            'readonly': True,
            },
        domain=[ #TODO descomentar despues de realizar la migracion
#            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
#                Eval('context', {}).get('company', -1)),
            ], select=True)
    number = fields.Char('Numeror', size=None, readonly=True, select=True)
    cia = fields.Many2One(
        'corseg.cia', 'Compania de Seguros', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
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
    pagos = fields.Many2Many(
        'poliza.pagos-liquidacion.cia',
        'liquidacion', 'pago', 'Pagos',
        domain=[
            #('company', '=', Eval('company')), #TODO descomentar despues de Migracion
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
        }, depends=['company', 'cia', 'state'])
    state = fields.Selection(_STATE, 'Estado',
        required=True, readonly=True)
    # TODO total
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
        super(LiquidacionCia, cls).__setup__()
        cls._order[0] = ('fecha', 'DESC')
        cls._error_messages.update({
                'delete_cancel': ('La Liquidacion "%s" debe estar '
                    'cancelada antes de eliminarse.'),
                'poliza_inicia': ('El primer movimiento para la poliza "%s" debe '
                    'ser un endoso de tipo Iniciacion.'),
                'poliza_un_inicia': ('Solo debe existir un movimiento de Iniciacion '
                    'de tipo endoso para la poliza "%s"'),
                'certificado_incluido': ('El certificado "%s" debe tener estado de '
                    '"Excluido" antes de la inclusion.'),
                'certificado_excluido': ('El certificado "%s" debe tener estado de '
                    '"Incluido" antes de la exclusion.'),
                'certificado_poliza': ('El certificado "%s" debe pertenecer a la '
                    'misma poliza del movimiento.'),
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

    @classmethod
    def set_number(cls, liqs):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        for liq in liqs:
            if liq.number:
                continue
            liq.number = \
                Sequence.get_id(liq.sequence.id)
        cls.save(liqs)

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if values.get('made_by') is None:
                values['made_by'] = Transaction().user
                values['made_date'] = get_current_date()
        liqs = super(LiquidacionCia, cls).create(vlist)
        return liqs

    @classmethod
    def delete(cls, liqs):
        for liq in liqs:
            if liq.state not in ['borrador', 'cancelado']:
                cls.raise_user_error('delete_cancel', (liq.rec_name,))
        super(LiquidacionCia, cls).delete(liqs)

    @classmethod
    @ModelView.button
    @Workflow.transition('borrador')
    def borrador(cls, liqs):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('procesado')
    def procesar(cls, liqs):
        for liq in liqs:
            set_auditoria(liq, 'processed')
            liq.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmado')
    def confirmar(cls, liqs):
        for liq in liqs:
            for pago in liq.pagos:
                # TODO verificar el state del pago
                pago.liq_cia = liq
                pago.state = 'liq_cia'
                pago.save()
            set_auditoria(liq, 'confirmed')
            liq.save()
        cls.set_number(liqs)
        # TODO crear el account_move

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, liqs):
        for liq in liqs:
            set_auditoria(liq, 'canceled')
            liq.save()


class LiquidacionVendedor(Workflow, ModelSQL, ModelView):
    'Liquidacion Comisiones Vendedor'
    __name__ = 'corseg.liquidacion.vendedor'
    company = fields.Many2One('company.company', 'Company', required=False, # TODO required=True
        states={
            'readonly': True,
            },
        domain=[ #TODO descomentar despues de realizar la migracion
#            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
#                Eval('context', {}).get('company', -1)),
            ], select=True)
    number = fields.Char('Numeror', size=None, readonly=True, select=True)
    vendedor = fields.Many2One('corseg.vendedor',
        'Vendedor', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
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
    pagos = fields.Many2Many(
        'poliza.pagos-liquidacion.vendedor',
        'liquidacion', 'pago', 'Pagos',
        domain=[
            #('company', '=', Eval('company')), #TODO descomentar despues de migracion
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
        }, depends=['company', 'vendedor', 'state'])
    state = fields.Selection(_STATE, 'Estado',
        required=True, readonly=True)
    # TODO total
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
        super(LiquidacionVendedor, cls).__setup__()
        cls._order[0] = ('fecha', 'DESC')
        cls._error_messages.update({
                'delete_cancel': ('La Liquidacion "%s" debe estar '
                    'cancelado antes de eliminarse.'),
                'poliza_inicia': ('El primer movimiento para la poliza "%s" debe '
                    'ser un endoso de tipo Iniciacion.'),
                'poliza_un_inicia': ('Solo debe existir un movimiento de Iniciacion '
                    'de tipo endoso para la poliza "%s"'),
                'certificado_incluido': ('El certificado "%s" debe tener estado de '
                    '"Excluido" antes de la inclusion.'),
                'certificado_excluido': ('El certificado "%s" debe tener estado de '
                    '"Incluido" antes de la exclusion.'),
                'certificado_poliza': ('El certificado "%s" debe pertenecer a la '
                    'misma poliza del movimiento.'),
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

    @classmethod
    def set_number(cls, liqs):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        for liq in liqs:
            if liq.number:
                continue
            liq.number = \
                Sequence.get_id(liq.sequence.id)
        cls.save(liqs)

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if values.get('made_by') is None:
                values['made_by'] = Transaction().user
                values['made_date'] = get_current_date()
        liqs = super(LiquidacionVendedor, cls).create(vlist)
        return liqs

    @classmethod
    def delete(cls, liqs):
        for liq in liqs:
            if liq.state not in ['borrador', 'cancelado']:
                cls.raise_user_error('delete_cancel', (liq.rec_name,))
        super(LiquidacionVendedor, cls).delete(liqs)

    @classmethod
    @ModelView.button
    @Workflow.transition('borrador')
    def borrador(cls, liqs):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('procesado')
    def procesar(cls, liqs):
        for liq in liqs:
            set_auditoria(liq, 'processed')
            liq.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmado')
    def confirmar(cls, liqs):
        for liq in liqs:
            for pago in liq.pagos:
                # TODO verificar el state del pago
                pago.liq_vendedor = liq
                pago.state = 'liq_vendedor'
                pago.save()
            set_auditoria(liq, 'confirmed')
            liq.save()
        cls.set_number(pagos)
        # TODO crear el account_move

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, liqs):
        for liq in liqs:
            set_auditoria(liq, 'canceled')
            liq.save()


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
