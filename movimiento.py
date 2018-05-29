#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, If, Bool, Equal, Not, In
from trytond.modules.company.model import (
        CompanyMultiValueMixin, CompanyValueMixin)

__all__ = [
        'Certificado', 'Movimiento',
        'Comentario', 'InclusionExclusion'
    ]


class Certificado(ModelSQL, ModelView):
    'Certificado'
    __name__ = 'corseg.poliza.certificado'
    poliza = fields.Many2One('corseg.poliza', 'Poliza', readonly=True)
    numero = fields.Char('Numero de Certificado', required=True)
    asegurado = fields.Many2One('corseg.poliza.asegurado', 'Asegurado', required=True,
            ondelete='CASCADE')
#    extendidos = fields.One2Many('corseg.poliza.extendido',
#        'certificado', 'Extendidos')
    notas = fields.Char('Notas', size=None)
    state = fields.Selection([
            ('new', 'Nuevo'),
            ('incluido', 'Incluido'),
            ('excluido', 'Excluido')
        ], 'Estado', required=True, readonly=True)

    # TODO datos tecnicos

    @staticmethod
    def default_state():
        return 'new'

    def get_rec_name(self, name):
        return self.numero + '-' + self.asegurado.rec_name


class Movimiento(Workflow, ModelSQL, ModelView):
    'Movimiento de Poliza'
    __name__ = 'corseg.poliza.movimiento'
    poliza = fields.Many2One('corseg.poliza', 'Poliza', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
    fecha = fields.Date('Fecha', required=True)
    descripcion = fields.Char('Descripcion', required=True,
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
        }, depends=['state'])
    tipo = fields.Selection([
            ('general', 'General'),
            ('endoso', 'Endoso'),
        ], 'Tipo', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),        
        }, depends=['state'])
    tipo_endoso = fields.Selection([
            ('iniciacion', 'Iniciacion'),
            ('renovacion', 'Renovacion'),
            ('otros', 'Otros'),
            ('finalizacion', 'Finalizacion'),
        ], 'Tipo Endoso',
        states={
            'invisible': Not(In(Eval('tipo'), ['endoso',])),
            'readonly': Not(In(Eval('state'), ['borrador',])),
            'required': In(Eval('tipo'), ['endoso',]),
        }, depends=['tipo']
    )
    contratante = fields.Many2One('party.party', 'Contratante',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    f_emision = fields.Date('Emitida el',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    f_desde = fields.Date('Vig. Desde',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    f_hasta = fields.Date('Vig. Hasta',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    suma_asegurada = fields.Numeric('Suma Asegurada', digits=(16, 2),
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    prima = fields.Numeric('Prima', digits=(16, 2),
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    forma_pago = fields.Many2One('corseg.forma_pago', 'Forma pago',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    frecuencia_pago = fields.Many2One('corseg.frecuencia_pago', 'Frecuencia pago',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    no_cuotas = fields.Integer('Cant. cuotas',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
        }, depends=['tipo_endoso'])
    inclu_exclu = fields.One2Many('corseg.poliza.inclu_exclu',
        'movimiento', 'Inclusion / Exclusion')
    comentario = fields.Text('Comentarios', size=None)
    state = fields.Selection([
            ('borrador', 'Borrador'),
            ('procesado', 'Procesado'),
            ('confirmado', 'Confirmado'),
            ('cancelado', 'Cancelado'),
        ], 'Estado', required=True, readonly=True)

    # TODO renovacion - correlativo de renovaciones

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
    def _act_poliza(name, poliza, mov):
        v = getattr(mov, name)
        if v:
            setattr(poliza, name, v)

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
        for mov in movs:
            pl = mov.poliza
            cls._act_poliza('contratante', pl, mov)
            pl.state = 'vigente'
            pl.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, movs):
        # TODO cambiar el state de la poliza,
        # si es su primer movimiento debe asignarse 'new'
        pass


class InclusionExclusion(ModelSQL, ModelView):
    'Inclusion /  Exclusion'
    __name__ = 'corseg.poliza.inclu_exclu'
    movimiento = fields.Many2One(
            'corseg.poliza.movimiento', 'Movimiento', required=True)
    poliza = fields.Function(fields.Many2One('corseg.poliza', 'Poliza'),
        'get_poliza', searcher='search_poliza')
    tipo = fields.Selection([
            ('inclusion', 'Inclusion'),
            ('exclusion', 'Exclusion')
        ], 'Tipo', required=True)
    certificado = fields.Many2One('corseg.poliza.certificado', 'Certificado',
            domain=[
                If(
                    In(Eval('tipo'), ['inclusion']),
                    ['OR',
                        ('state', '=', 'new'),
                        [
                            ('poliza', '=', Eval('poliza')),
                            ('state', '=', 'excluido'),
                        ]
                    ],
                    [
                        ('poliza', '=', Eval('poliza')),
                        ('state', '=', 'incluido')
                    ]
                )
            ],
            depends=['poliza', 'tipo']
    )

#    @classmethod
#    def create(cls, vlist):
#        inclu_exclus = super(InclusionExclusion, cls).create(vlist)
#        for ie in inclu_exclus:
#            if ie.tipo == 'inclusion':
#                if ie.certificado.state not in ['new', 'excluido']:
#                    raise Exception(
#                        "El certificado debe estar en un estado 'Nuevo' o 'Excluido' " \
#                        "para poder ser incluido.")
#                ie.certificado.state = 'incluido'
#            elif ie.tipo == 'exclusion':
#                if ie.certificado.state not in ['incluido']:
#                    raise Exception(
#                        "El certificado debe estar en un estado 'Incluido' " \
#                        "para poder ser excluido.")
#                ie.certificado.state = 'excluido'
#            ie.certificado.save()
#        return inclu_exclus

    def get_poliza(self, name):
        if self.movimiento:
            return self.movimiento.poliza


class Comentario(ModelSQL, ModelView):
    'Comentarios sobre la Poliza'
    __name__ = 'corseg.poliza.comentario'
    poliza = fields.Many2One(
            'corseg.poliza', 'Poliza', required=True)
    fecha = fields.Date('Fecha', required=True)
    comentario = fields.Text('Comentario', size=None)
