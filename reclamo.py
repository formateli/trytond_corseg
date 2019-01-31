#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
from trytond.transaction import Transaction
from trytond.pool import Pool
from trytond.model import Workflow, ModelSQL, ModelView, fields
from trytond.pyson import Eval, If, Bool, Not, In, And
from trytond.modules.corseg.tools import \
        auditoria_field, get_current_date, set_auditoria


__all__ = [
        'Reclamo',
        'ReclamoComentario',
        'ReclamoDocumento'
    ]

_STATES={
        'readonly': Not(In(Eval('state'), ['borrador',])),
    }

_DEPENDS=['state']


class Reclamo(Workflow, ModelSQL, ModelView):
    'Reclamo'
    __name__ = 'corseg.poliza.reclamo'
    company = fields.Many2One('company.company', 'Company', required=True,
        states={
            'readonly': True,
            },
        domain=[
            ('id', If(Eval('context', {}).contains('company'), '=', '!='),
                Eval('context', {}).get('company', -1)),
            ], select=True)
    number = fields.Char('Numero', size=None, readonly=True, select=True)
    currency = fields.Many2One('currency.currency',
        'Moneda', required=True, states={'readonly': True})
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'get_currency_digits')
    poliza = fields.Many2One('corseg.poliza', 'Poliza', required=True,
        domain=[
            ('company', '=', Eval('company')),
            If(
                In(Eval('state'), ['borrador']),
                [('state', '!=', 'cancelado')],
                [('state', '!=', '')]
            )
        ],
        states=_STATES, depends=['company', 'state'])
    cia = fields.Function(
        fields.Many2One('corseg.cia', 'Compania de Seguros'),
        'get_cia', searcher='search_cia')
    contratante = fields.Function(
        fields.Many2One('party.party', 'Contratante'),
        'get_contratante', searcher='search_contratante')
    renovacion = fields.Integer('Renovacion', required=True,
        states={'readonly': True})
    fecha = fields.Date('Fecha', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['borrador', 'procesado'])),
        }, depends=['state'])
    fecha_recibido = fields.Date('Fecha Recibido',
        states={
            'required': In(Eval('state'), ['recibido',]),
            'readonly': Not(In(Eval('state'), [
                    'borrador', 'incompleto', 'recibido',
                ])),
        }, depends=['state'])
    fecha_finiquito = fields.Date('Fecha Finiquito',
        states={
            'required': In(Eval('state'), ['finiquito',]),
            'readonly': Not(In(Eval('state'), ['finiquito',])),
            'invisible': Not(In(Eval('state'), ['aprobado', 'finiquito',])),
        }, depends=['state'])
    referencia = fields.Char('Referencia')
    monto_reclamado = fields.Numeric('Monto Reclamado', required=True,
        digits=(16, Eval('currency_digits', 2)),
        states=_STATES, depends=['currency_digits'])
    deducible = fields.Numeric('Deducible', required=True,
        digits=(16, Eval('currency_digits', 2)),
        states=_STATES, depends=['currency_digits'])
    monto_aprobado = fields.Numeric('Monto Aprobado', required=True,
        digits=(16, Eval('currency_digits', 2)),
        states=_STATES, depends=['currency_digits'])
    descripcion = fields.Text('Descripcion', size=None,
        states={
            'readonly': Not(In(Eval('state'), ['borrador', 'procesado'])),
        }, depends=['state'])
    comentarios = fields.One2Many('corseg.poliza.reclamo.comentario',
        'reclamo', 'Comentarios')
    documentos = fields.One2Many('corseg.poliza.reclamo.documento',
        'reclamo', 'Documentos')
    state = fields.Selection([
            ('borrador', 'Borrador'),
            ('incompleto', 'Incompleto'),
            ('recibido', 'Recibido'),
            ('aprobado', 'Aprobado'),
            ('rechazado', 'Rechazado'),
            ('reconsiderado', 'Reconsiderado'),
            ('finiquito', 'Finiquito'),
            ('cancelado', 'Cancelado'),
        ], 'Estado', required=True, readonly=True)
    made_by = auditoria_field('user', 'Creado por')
    made_date = auditoria_field('date', 'fecha')
    incompleto_by = auditoria_field('user', 'Incompleto por')
    incompleto_date = auditoria_field('date', 'fecha')
    recibido_by = auditoria_field('user', 'Recibido por')
    recibido_date = auditoria_field('date', 'fecha')
    aprobado_by = auditoria_field('user', 'Aprobado por')
    aprobado_date = auditoria_field('date', 'fecha')
    rechazado_by = auditoria_field('user', 'Rechazado por')
    rechazado_date = auditoria_field('date', 'fecha')
    reconsiderado_by = auditoria_field('user', 'Reconsiderado por')
    reconsiderado_date = auditoria_field('date', 'fecha')
    finiquito_by = auditoria_field('user', 'Finiquito por')
    finiquito_date = auditoria_field('date', 'fecha')
    canceled_by = auditoria_field('user', 'Cancelado por')
    canceled_date = auditoria_field('date', 'fecha')

    @classmethod
    def __setup__(cls):
        super(Reclamo, cls).__setup__()
        cls._order = [
                ('number', 'DESC'),
                ('fecha', 'DESC'),
            ]

        cls._error_messages.update({
                'delete_cancel': ('El registro "%s" debe estar '
                    'cancelado antes de eliminarse.'),
                'poliza_state': ('La poliza asociada al registro "%s" debe estar '
                    'en estado "Nuevo".'),
                'not_lineas': ('La Cotizacion "%s" no registra '
                    'ninguna linea.'),
                'not_seleccion': ('La Cotizacion "%s" debe tener '
                    'al menos una linea seleccionada.'),
                })

        cls._transitions |= set(
            (
                ('borrador', 'incompleto'),
                ('borrador', 'recibido'),
                ('incompleto', 'recibido'),
                ('incompleto', 'cancelado'),
                ('recibido', 'aprobado'),
                ('recibido', 'rechazado'),
                ('rechazado', 'reconsiderado'),
                ('reconsiderado', 'rechazado'),
                ('reconsiderado', 'aprobado'),
                ('aprobado', 'finiquito'),
            )
        )

        cls._buttons.update({
            'cancelar': {
                'invisible': Not(In(Eval('state'), ['incompleto',])),
                },
            'incompleto': {
                'invisible': Not(In(Eval('state'), ['borrador'])),
                },
            'recibir': {
                'invisible': Not(In(Eval('state'), ['borrador', 'incompleto'])),
                },
            'aprobar': {
                'invisible': Not(In(Eval('state'), ['recibido', 'reconsiderado'])),
                },
            'rechazar': {
                'invisible': Not(In(Eval('state'), ['recibido', 'reconsiderado'])),
                },
            'reconsiderar': {
                'invisible': Not(In(Eval('state'), ['rechazado',])),
                },
            'finiquitar': {
                'invisible': Not(In(Eval('state'), ['aprobado',])),
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
        return str(self.id)

    @classmethod
    def search_rec_name(cls, name, clause):
        return [('number',) + tuple(clause[1:])]

    def get_cia(self, name):
        if self.poliza:
            return self.poliza.cia.id

    def get_contratante(self, name):
        if self.poliza and self.poliza.contratante:
            return self.poliza.contratante.id

    @classmethod
    def search_cia(cls, name, clause):
        return [('poliza.cia',) + tuple(clause[1:])]

    @classmethod
    def search_contratante(cls, name, clause):
        return [('poliza.contratante',) + tuple(clause[1:])]


class ReclamoComentario(ModelSQL, ModelView):
    'Comentarios sobre Reclamo'
    __name__ = 'corseg.poliza.reclamo.comentario'
    reclamo = fields.Many2One('corseg.poliza.reclamo', 'Reclamo',
        ondelete='CASCADE', select=True, required=True)
    fecha = fields.Date('Fecha', required=True)
    comentario = fields.Text('Comentario', size=None)

    @classmethod
    def __setup__(cls):
        super(ReclamoComentario, cls).__setup__()
        cls._order = [
                ('fecha', 'DESC'),
                ('id', 'DESC'),
            ]

    @staticmethod
    def default_fecha():
        pool = Pool()
        Date = pool.get('ir.date')
        return Date.today()


class ReclamoDocumento(ModelSQL, ModelView):
    'Documento Reclamo'
    __name__ = 'corseg.poliza.reclamo.documento'

    reclamo = fields.Many2One('corseg.poliza.reclamo', 'Reclamo',
        ondelete='CASCADE', select=True, required=True)
    name = fields.Char('Nombre', required=True)
    comentario = fields.Text('Comentario', size=None)
    documento = fields.Binary('Documento', file_id='doc_id',
        required=True)
    doc_id = fields.Char('Doc id',
            states={'invisible': True}
        )
