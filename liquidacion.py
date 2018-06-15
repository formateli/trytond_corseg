#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, Bool, If, Not, In

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
    # TODO numero
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
    # TODO procesado_por, confirmado_por, cancelado_por

    @classmethod
    def __setup__(cls):
        super(LiquidacionCia, cls).__setup__()
        cls._order[0] = ('fecha', 'DESC')
        cls._error_messages.update({
                'delete_cancel': ('El movimiento "%s" debe ser '
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
    @ModelView.button
    @Workflow.transition('borrador')
    def borrador(cls, liqs):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('procesado')
    def procesar(cls, liqs):
        pass

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
        # TODO crear el account_move

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, liqs):
        pass


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
    # TODO numero
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
    # TODO procesado_por, confirmado_por, cancelado_por

    @classmethod
    def __setup__(cls):
        super(LiquidacionVendedor, cls).__setup__()
        cls._order[0] = ('fecha', 'DESC')
        cls._error_messages.update({
                'delete_cancel': ('El movimiento "%s" debe ser '
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
    @ModelView.button
    @Workflow.transition('borrador')
    def borrador(cls, liqs):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('procesado')
    def procesar(cls, liqs):
        pass

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
        # TODO crear el account_move

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, liqs):
        pass


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

