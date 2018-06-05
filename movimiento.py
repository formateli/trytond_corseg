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
    company = fields.Many2One('company.company', 'Company', required=False, # TODO required=True
        states={
            'readonly': True,
            },
        domain=[ #TODO descomentar despues de realizar la migracion
#            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
#                Eval('context', {}).get('company', -1)),
            ], select=True)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'get_currency_digits')
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
            ('none', ''),
            ('iniciacion', 'Iniciacion'),
            ('renovacion', 'Renovacion'),
            ('otros', 'Otros'),
            ('cancelacion', 'Cancelacion'),
            ('anulacion', 'Anulacion'),
        ], 'Tipo Endoso',
        states={
            'invisible': Not(In(Eval('tipo'), ['endoso'])),
            'readonly': Not(In(Eval('state'), ['borrador'])),
            'required': In(Eval('tipo'), ['endoso']),
        }, depends=['tipo', 'state']
    )
    contratante = fields.Many2One('party.party', 'Contratante',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=_DEPENDS)
    f_emision = fields.Date('Emitida el',
        states=_STATES, depends=_DEPENDS)
    f_desde = fields.Date('Vig. Desde',
        states=_STATES, depends=_DEPENDS)
    f_hasta = fields.Date('Vig. Hasta',
        states=_STATES, depends=_DEPENDS)
    suma_asegurada = fields.Numeric('Suma Asegurada',
        digits=(16, Eval('currency_digits', 2)),
        states=_STATES,
        depends=_DEPENDS + ['currency_digits'])
    prima = fields.Numeric('Prima',
        digits=(16, Eval('currency_digits', 2)),
        states=_STATES,
        depends=_DEPENDS + ['currency_digits'])
    vendedor = fields.Many2One('corseg.vendedor', 'Vendedor',
        states={
            'required': In(Eval('tipo_endoso'), ['iniciacion',]),
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=_DEPENDS)
    forma_pago = fields.Many2One('corseg.forma_pago', 'Forma pago',
        states=_STATES, depends=_DEPENDS)
    frecuencia_pago = fields.Many2One('corseg.frecuencia_pago',
        'Frecuencia pago',
        states=_STATES, depends=_DEPENDS)
    no_cuotas = fields.Integer('Cant. cuotas',
        states=_STATES, depends=_DEPENDS)
    inclu_exclu = fields.One2Many('corseg.poliza.inclu_exclu',
        'movimiento', 'Inclusion / Exclusion',
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
    comentario = fields.Text('Comentarios', size=None,
        states={
            'readonly': In(Eval('state'), ['confirmado',]),
        }, depends=['state'])
    state = fields.Selection([
            ('borrador', 'Borrador'),
            ('procesado', 'Procesado'),
            ('confirmado', 'Confirmado'),
            ('cancelado', 'Cancelado'),
        ], 'Estado', required=True, readonly=True)

    # TODO procesado_por, confirmado_por, cancelado_por

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
    def default_currency_digits():
        return 2

    @fields.depends('poliza', 'currency_digits')
    def on_change_poliza(self):
        self.currency_digits = 2
        if self.poliza:
            self.currency_digits = \
                self.poliza.currency_digits

    def get_currency_digits(self, name=None):
        if self.poliza:
            self.poliza.currency_digits
        return 2

    @staticmethod
    def _act_poliza(name, poliza, mov):
        v = getattr(mov, name)
        if v is not None:
            setattr(poliza, name, v)
            
    @classmethod
    def _get_poliza_fields(cls):
        fields = ['contratante', 'f_emision',
            'f_desde', 'f_hasta', 'suma_asegurada',
            'prima', 'forma_pago', 'frecuencia_pago',
            'no_cuotas', 'vendedor']
        return fields

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
            if mov.tipo_endoso == 'cancelacion':
                pl.state = 'cancelada'
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


class InclusionExclusion(ModelSQL, ModelView):
    'Inclusion /  Exclusion'
    __name__ = 'corseg.poliza.inclu_exclu' # TODO corseg.poliza.certificado.inclu_exclu
    movimiento = fields.Many2One(
            'corseg.poliza.movimiento', 'Movimiento', required=True)
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
                        ('poliza', '=',
                            Eval('_parent_movimiento', {}).get('poliza', -1)),
                        ('state', '=', 'excluido'),
                    ]
                ],
                [
                    ('poliza', '=',
                        Eval('_parent_movimiento', {}).get('poliza', -1)),
                    ('state', '=', 'incluido')
                ]
            )
        ],
        depends=['poliza', 'tipo']
    )

