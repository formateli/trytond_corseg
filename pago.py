#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, If, Not, In

__all__ = [
        'Certificado', 'Movimiento',
        'InclusionExclusion',
    ]


_STATES={
        'required': In(Eval('tipo_endoso'),
            ['iniciacion', 'renovacion']),
        'readonly': Not(In(Eval('state'), ['borrador',])),
    }

_DEPENDS=['tipo_endoso', 'state']


class Pago(Workflow, ModelSQL, ModelView):
    'Pago a Poliza'
    __name__ = 'corseg.poliza.pago'
    company = fields.Many2One('company.company', 'Company', required=False, # TODO required=True
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    # TODO numero
    poliza = fields.Many2One('corseg.poliza', 'Poliza', required=True,
        domain=[
            ('company', '=', Eval('company')),
            If(
                In(Eval('state'), ['confirmado']),
                [('state', '!=', '')],
                [('state', '!=', 'finalizada')]
            )
        ],
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['company', 'state'])
    fecha = fields.Date('Fecha', required=True,
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
        }, depends=['state'])
    referencia = fields.Char('Referencia', required=True,
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
        }, depends=['state'])
    monto = fields.Numeric('Monto', digits=(16, 2),
        states=_STATES, depends=_DEPENDS)
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=_DEPENDS)
    comentario = fields.Text('Comentarios', size=None,
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
        }, depends=['state'])
    state = fields.Selection([
            ('borrador', 'Borrador'),
            ('procesado', 'Procesado'),
            ('confirmado', 'Confirmado'),
            ('liq_cia', 'Liquidado por Cia. de Seguros'),
            ('liq_vendedor', 'Liquidado a Vendedor'),
        ], 'Estado', required=True, readonly=True)

    @classmethod
    def __setup__(cls):
        super(Movimiento, cls).__setup__()
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
    def borrador(cls, movs):
        pass

    @classmethod
    @ModelView.button
    @Workflow.transition('procesado')
    def procesar(cls, movs):
        for mov in movs:
            if mov.poliza.state == 'new' and \
                    mov.tipo_endoso != 'iniciacion':
                cls.raise_user_error(
                    'poliza_inicia',
                    (mov.poliza.rec_name,))
            if mov.poliza.state == 'vigente' and \
                    mov.tipo_endoso == 'iniciacion':
                cls.raise_user_error(
                    'poliza_un_inicia',
                    (mov.poliza.rec_name,))

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmado')
    def confirmar(cls, movs):
        fields = cls._get_poliza_fields()
        for mov in movs:
            pl = mov.poliza
            for f in fields:
                cls._act_poliza(f, pl, mov)
            if mov.tipo_endoso == 'finalizacion':
                pl.state = 'finalizada'
            else:
                pl.state = 'vigente'
            pl.save()

            for ie in mov.inclu_exclu:
                cert = ie.certificado
                if ie.tipo == 'inclusion' and \
                        cert.state != 'new':
                    if cert.state != 'excluido':
                        cls.raise_user_error(
                            'certificado_excluido',
                            (cert.rec_name,))
                    if cert.poliza.id != pl.id:
                        cls.raise_user_error(
                            'certificado_poliza',
                            (cert.rec_name,))
                elif ie.tipo == 'exclusion' and \
                        cert.state != 'incluido':
                    cls.raise_user_error(
                        'certificado_incluido',
                        (cert.rec_name,))
                elif ie.tipo == 'exclusion' and \
                        cert.poliza.id != pl.id:
                    cls.raise_user_error(
                        'certificado_poliza',
                        (cert.rec_name,))

                if ie.tipo == 'inclusion':
                    cert.state = 'incluido'
                else:
                    cert.state = 'excluido'
                cert.poliza = pl
                cert.save()
                ie.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, movs):
        # TODO cambiar el state de la poliza,
        # si es su primer movimiento debe asignarse 'new'
        pass
