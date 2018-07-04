#This file is part of tryton-corseg project. The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.

from trytond.pool import Pool, PoolMeta
from trytond.transaction import Transaction
from trytond.model import Workflow, ModelView, ModelSQL, fields
from trytond.pyson import Eval, If, Not, In, Bool
from .tools import auditoria_field, get_current_date, set_auditoria

__all__ = [
        'PartyCorseg',
        'Certificado',
        'CertificadoInclusion',
        'CertificadoExclusion',
        'CertificadoModificacion',
        'Extension',
        'ExtendidoInclusion',
        'ExtendidoExclusion',
        'Movimiento',
    ]


_STATES={
        'required': In(Eval('tipo_endoso'),
            ['iniciacion', 'renovacion']),
        'readonly': Not(In(Eval('state'), ['borrador',])),
    }

_DEPENDS=['tipo_endoso', 'state']


class PartyCorseg:
    __metaclass__ = PoolMeta
    __name__ = 'party.party'
    asegurado_certs = fields.One2Many(
        'corseg.poliza.certificado',
        'asegurado', 'Certificados', readonly=True)
    extendido_certs = fields.One2Many(
        'corseg.poliza.certificado.extension',
        'extendido', 'Extensiones', readonly=True)


class Certificado(ModelSQL, ModelView):
    'Certificado'
    __name__ = 'corseg.poliza.certificado'
    poliza = fields.Many2One('corseg.poliza', 'Poliza', readonly=True)
    numero = fields.Char('Numero', required=True,
        states={
            'readonly': Not(In(Eval('state'), ['new',])),
        })
    asegurado = fields.Many2One('party.party', 'Asegurado',
        required=True, ondelete='CASCADE',
        states={
            'readonly': Not(In(Eval('state'), ['new',])),
        })
    suma_asegurada = fields.Numeric('Suma Asegurada',
        digits=(16, 2),
        states={
            'readonly': Not(In(Eval('state'), ['new',])),
        })
    prima = fields.Numeric('Prima',
        digits=(16, 2),
        states={
            'readonly': Not(In(Eval('state'), ['new',])),
        })
    descripcion = fields.Text('Descripcion', size=None)
    extendidos = fields.One2Many(
        'corseg.poliza.certificado.extension',
        'certificado', 'Extendidos',
        states={
            'readonly': Not(In(Eval('state'), ['new',]))
        })
    # TODO incluidos y excluidos con filter sobre extendido
    vehiculo = fields.One2Many('corseg.vehiculo',
        'certificado', 'Vehiculo',
        size=None, # TODO deberia ser 1, pero en estos momentos no funciona con SAO
        states={
            'readonly': Not(In(Eval('state'), ['new',])),
        })
    state = fields.Selection([
            ('new', 'Nuevo'),
            ('incluido', 'Incluido'),
            ('excluido', 'Excluido')
        ], 'Estado', required=True, readonly=True)

    @staticmethod
    def default_state():
        return 'new'

    def get_rec_name(self, name):
        return self.numero + '-' + self.asegurado.rec_name


class Extension(ModelSQL, ModelView):
    'Extension'
    __name__ = 'corseg.poliza.certificado.extension'
    certificado = fields.Many2One('corseg.poliza.certificado',
        'Certificado',
        states={
            'invisible': Not(Bool(Eval('_parent_certificado'))),
        })
    extendido = fields.Many2One('party.party', 'Extendido',
        required=True, ondelete='CASCADE',
        states={
            'readonly': Not(In(Eval('state'), ['new',])),
        })
    state = fields.Selection([
            ('new', 'Nuevo'),
            ('incluido', 'Incluido'),
            ('excluido', 'Excluido')
        ], 'Estado', required=True, readonly=True)

    @staticmethod
    def default_state():
        return 'new'

    def get_rec_name(self, name):
        return self.extendido.rec_name


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
    number = fields.Char('Numero', size=None, readonly=True, select=True)
    currency_digits = fields.Function(fields.Integer('Currency Digits'),
        'get_currency_digits')
    poliza = fields.Many2One('corseg.poliza', 'Poliza', required=True,
        domain=[
#            ('company', '=', Eval('company')), # TODO Uncomment despues de migracion
            If(
                In(Eval('state'), ['confirmado']),
                [('state', '!=', '')],
                [('state', '!=', 'cancelada')]
            )
        ],
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['company', 'state'])
    poliza_state = fields.Function(fields.Char('Estado'),
        'get_poliza_state')
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
            (None, ''),
            ('iniciacion', 'Iniciacion'),
            ('renovacion', 'Renovacion'),
            ('otros', 'Otros'),
            ('cancelacion', 'Cancelacion'),
            ('anulacion', 'Anulacion'),
        ], 'Tipo Endoso',
        states={
            'invisible': Not(In(Eval('tipo'), ['endoso'])),
            'readonly': Not(In(Eval('state'), ['borrador'])),
        }, depends=['tipo', 'state']
    )
    numero = fields.Char('Numero de Poliza',
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state'])
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
    inclusiones = fields.Many2Many(
        'poliza.certificado-inclusion-poliza.movimiento',
        'movimiento', 'certificado', 'Inclusiones',
        domain=[
            If(
                In(Eval('state'), ['confirmado',]),
                [
                    ('poliza', '=', Eval('poliza')),
                    ('state', '=', 'incluido')
                ],
                ['OR',
                    [('state', '=', 'new')],
                    [
                        ('poliza', '=', Eval('poliza')),
                        ('state', '=', 'excluido'),
                    ]
                ],
            )
        ],
        states={
            'invisible': Not(Bool(Eval('poliza'))),
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['poliza', 'state'])
    exclusiones = fields.Many2Many(
        'poliza.certificado-exclusion-poliza.movimiento',
        'movimiento', 'certificado', 'Exclusiones',
        domain=[
            ('poliza', '=', Eval('poliza')),
            If(
                In(Eval('state'), ['confirmado',]),
                ('state', '=', 'excluido'),
                ('state', '=', 'incluido')
            )
        ],
        states={
            'invisible': Not(Bool(Eval('poliza'))),
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['poliza', 'state'])
    modificaciones = fields.One2Many(
        'corseg.poliza.certificado.modificacion',
        'movimiento', 'Modificaciones',
        states={
            'invisible': Not(Bool(Eval('poliza'))),
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['poliza', 'state'])
    comision_cia = fields.One2Many(
        'corseg.comision.movimiento.cia',
        'parent', 'Comision Cia',
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),            
        }, depends=['state'])
    comision_vendedor = fields.One2Many(
        'corseg.comision.movimiento.vendedor',
        'parent', 'Comision Vendedor',
        states={
            'readonly': Not(In(Eval('state'), ['borrador',])),
        }, depends=['state', 'vendedor'])
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
        super(Movimiento, cls).__setup__()
        cls._order = [
                ('number', 'DESC'),
                ('fecha', 'DESC'),
            ]
        cls._error_messages.update({
                'delete_cancel': ('El movimiento "%s" debe estar '
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
                'extension_certificado_nuevo': ('El estado del extendido "%s" debe '
                    'debe ser "Nuevo" para los certificados nuevos.'),
                'extendido_incluido': ('El extendido "%s" debe tener estado de '
                    '"Nuevo" o "Excluido" antes de la inclusion.'),
                'extendido_excluido': ('El extendido "%s" debe tener estado de '
                    '"Incluido" antes de la exclusion.'),
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

    @staticmethod
    def default_state():
        return 'borrador'

    @staticmethod
    def default_tipo_endoso():
        return None

    @fields.depends('tipo', 'tipo_endoso')
    def on_change_tipo(self):
        self.tipo_endoso = None

    @fields.depends('poliza', 'currency_digits', 'poliza_state')
    def on_change_poliza(self):
        self.poliza_state = None
        self.currency_digits = 2
        if self.poliza:
            self.currency_digits = \
                self.poliza.currency_digits
            self.poliza_state = self.poliza.state

    def get_currency_digits(self, name=None):
        if self.poliza:
            self.poliza.currency_digits
        return 2

    def get_poliza_state(self, name=None):
        if self.poliza:
            return self.poliza.state

    def _fill_comision(self, parent, Comision, lineas):
        print("fill...")
        for cm in lineas:
            print("  fill")
            new = Comision()
            new.parent = parent
            new.renovacion = cm.renovacion
            new.tipo_comision = cm.tipo_comision
            new.re_renovacion = cm.re_renovacion
            new.re_cuota = cm.re_cuota
            new.active = cm.active
            new.save()

    def _set_default_inclusion(self):
        if self.inclusiones:
            return
        Certificado = Pool().get(
            'corseg.poliza.certificado')
        certificado = Certificado(
            numero='1',
            asegurado=self.contratante,
        )
        certificado.save()
        self.inclusiones = [certificado,]

    def _prepare_comision_inicio(self):
        pool = Pool()
        ComisionMovimientoCia = pool.get(
            'corseg.comision.movimiento.cia')
        ComisionMovimientoVendedor = pool.get(
            'corseg.comision.movimiento.vendedor')

        if not self.comision_cia and \
                self.poliza.cia_producto.comision_cia:
            print("fill_mov_cia")
            self._fill_comision(
                self, ComisionMovimientoCia,
                self.poliza.cia_producto.comision_cia.lineas)

        if not self.comision_vendedor:
            if self.poliza.cia_producto.comision_vendedor:
                found = False
                for vnd in self.poliza.cia_producto.comision_vendedor.lineas:
                    if vnd.vendedor.id == self.vendedor.id:
                        self._fill_comision(
                            self, ComisionMovimientoVendedor,
                            vnd.comision.lineas)
                        found = True
                        break
                if not found:
                    self._set_comision_vendedor_defecto(
                        ComisionMovimientoVendedor)                    
            else:
                self._set_comision_vendedor_defecto(
                    ComisionMovimientoVendedor)

    def _set_comision_vendedor_defecto(self, ComisionMovimientoVendedor):
        if self.poliza.cia_producto.comision_vendedor_defecto:
            self._fill_comision(
                self, ComisionMovimientoVendedor,
                self.poliza.cia_producto.comision_vendedor_defecto.lineas)        

    def _set_comision(self):
        pool = Pool()
        ComisionPolizaCia = pool.get(
            'corseg.comision.poliza.cia')
        ComisionPolizaVendedor = pool.get(
            'corseg.comision.poliza.vendedor')

        if self.comision_cia:
            ComisionPolizaCia.delete(
                [com for com in self.poliza.comision_cia])
            self._fill_comision(self.poliza,
                ComisionPolizaCia, self.comision_cia)

        if self.comision_vendedor:
            ComisionPolizaVendedor.delete(
                [com for com in self.poliza.comision_vendedor])
            self._fill_comision(self.poliza,
                ComisionPolizaVendedor, self.comision_vendedor)

    @staticmethod
    def _act_field(name, obj, chg):
        v = getattr(chg, name)
        if v is not None:
            try:
                if v == '' or v == 'none':
                    return
            except:
                pass
            setattr(obj, name, v)
            
    @classmethod
    def _get_poliza_fields(cls):
        fields = ['numero', 'contratante', 'f_emision',
            'f_desde', 'f_hasta', 'suma_asegurada',
            'prima', 'forma_pago', 'frecuencia_pago',
            'no_cuotas', 'vendedor']
        return fields

    @classmethod
    def _get_cert_fields(cls):
        fields = ['numero', 'asegurado',
            'suma_asegurada', 'prima',
            'descripcion']
        return fields

    @classmethod
    def _get_vehiculo_fields(cls):
        fields = ['placa', 'marca', 'modelo',
            'ano', 's_motor', 's_carroceria',
            'color', 'transmision', 'uso', 'tipo']
        return fields

    @classmethod
    def set_number(cls, movs):
        pool = Pool()
        Sequence = pool.get('ir.sequence')
        Config = pool.get('corseg.configuration')
        config = Config(1)
        for mov in movs:
            if mov.number:
                continue
            mov.number = Sequence.get_id(config.movimiento_seq.id)
        cls.save(movs)

    @classmethod
    def create(cls, vlist):
        vlist = [x.copy() for x in vlist]
        for values in vlist:
            if values.get('made_by') is None:
                values['made_by'] = Transaction().user
                values['made_date'] = get_current_date()
        movs = super(Movimiento, cls).create(vlist)
        return movs

    @classmethod
    def delete(cls, movs):
        for mov in movs:
            if mov.state not in ['borrador', 'cancelado']:
                cls.raise_user_error('delete_cancel', (mov.rec_name,))
        super(Movimiento, cls).delete(movs)

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
            if mov.poliza.state in ['vigente', 'cancelada'] and \
                    mov.tipo_endoso == 'iniciacion':
                cls.raise_user_error(
                    'poliza_un_inicia',
                    (mov.poliza.rec_name,))
            if mov.tipo_endoso == 'iniciacion':
                mov._set_default_inclusion()
                mov._prepare_comision_inicio()
            set_auditoria(mov, 'processed')
            mov.save()

    @classmethod
    @ModelView.button
    @Workflow.transition('confirmado')
    def confirmar(cls, movs):
        pool = Pool()
        Vehiculo = pool.get('corseg.vehiculo')
        fields = cls._get_poliza_fields()
        fields_cert = cls._get_cert_fields()
        fields_vehiculo = cls._get_vehiculo_fields()
        for mov in movs:
            pl = mov.poliza
            for f in fields:
                cls._act_field(f, pl, mov)
            if mov.tipo_endoso == 'cancelacion':
                pl.state = 'cancelada'
            else:
                pl.state = 'vigente'
            if mov.tipo_endoso == 'iniciacion':
                pl.renovacion = 0
            elif mov.tipo_endoso == 'renovacion':
                pl.renovacion += 1 
            pl.save()

            for cert in mov.inclusiones:
                if cert.state != 'new':
                    if cert.state != 'excluido':
                        cls.raise_user_error(
                            'certificado_excluido',
                            (cert.rec_name,))
                    if cert.poliza.id != pl.id:
                        cls.raise_user_error(
                            'certificado_poliza',
                            (cert.rec_name,))
                else:
                    for ext in cert.extendidos:
                        if ext.state != 'new':
                            cls.raise_user_error(
                                'extension_certificado_nuevo',
                                (ext.rec_name,))
                        ext.state = 'incluido'
                        ext.save()
                cert.state = 'incluido'
                cert.poliza = pl
                cert.save()

            for cert in mov.exclusiones:
                if cert.state != 'incluido':
                    cls.raise_user_error(
                        'certificado_incluido',
                        (cert.rec_name,))
                if cert.poliza.id != pl.id:
                    cls.raise_user_error(
                        'certificado_poliza',
                        (cert.rec_name,))
                cert.state = 'excluido'
                cert.poliza = pl
                cert.save()

            mov._set_comision()

            for mod in mov.modificaciones:
                for f in fields_cert:
                    cls._act_field(f, mod.certificado, mod)
                mod.certificado.save()

                if mod.vehiculo:
                    if mod.certificado.vehiculo:
                        vehiculo = mod.certificado.vehiculo[0]
                    else:
                        # Creamos un vehiculo nuevo
                        vehiculo = Vehiculo()
                        vehiculo.certificado = mod.certificado

                    for f in fields_vehiculo:
                        cls._act_field(
                            f, vehiculo, mod.vehiculo[0])
                    vehiculo.save()

                for ext in mod.inclusiones:
                    if ext.state not in ['new', 'excluido']:
                        cls.raise_user_error(
                            'extendido_excluido',
                            (ext.rec_name,))
                    if ext.state == 'new':
                        ext.certificado = mod.certificado
                    ext.state = 'incluido'
                    ext.save()

                for ext in mod.exclusiones:
                    if ext.state not in ['incluido']:
                        cls.raise_user_error(
                            'extendido_incluido',
                            (ext.rec_name,))
                    ext.state = 'excluido'
                    ext.save()

                mod.state = 'confirmado'
                mod.save()

            set_auditoria(mov, 'confirmed')
            mov.save()

        cls.set_number(movs)

    @classmethod
    @ModelView.button
    @Workflow.transition('cancelado')
    def cancelar(cls, movs):
        for mov in movs:
            set_auditoria(mov, 'canceled')
            mov.save()


class CertificadoModificacion(ModelSQL, ModelView):
    'Modificacion de Certificado'
    __name__ = 'corseg.poliza.certificado.modificacion'
    movimiento = fields.Many2One('corseg.poliza.movimiento',
        'Movimiento', ondelete='CASCADE', select=True, required=True)
    certificado = fields.Many2One('corseg.poliza.certificado',
        'Certificado', ondelete='CASCADE', select=True, required=True,
        domain=[
            ('poliza', '=',
                Eval('_parent_movimiento', {}).get('poliza', -1)),
        ])
    inclusiones = fields.Many2Many(
        'poliza.certificado-inclusion-certificado.extendido',
        'modificacion', 'extendido', 'Inclusiones',
        domain=[
            If(
                In(Eval('state'), ['confirmado',]),
                [
                    ('certificado', '=', Eval('certificado')),
                    ('state', '=', 'incluido')
                ],
                ['OR',
                    [('state', '=', 'new')],
                    [
                        ('certificado', '=', Eval('certificado')),
                        ('state', '=', 'excluido'),
                    ]
                ],
            )
        ],
        states={
            'readonly': Not(In(Eval('state'), ['new',])),
            'invisible': Not(Bool(Eval('certificado'))),
        }, depends=['certificado', 'state'])
    exclusiones = fields.Many2Many(
        'poliza.certificado-exclusion-certificado.extendido',
        'modificacion', 'extendido', 'Exclusiones',
        domain=[
            ('certificado', '=', Eval('certificado')),
            If(
                In(Eval('state'), ['confirmado',]),
                ('state', '=', 'excluido'),
                ('state', '=', 'incluido')
            )
        ],
        states={
            'readonly': Not(In(Eval('state'), ['new',])),
            'invisible': Not(Bool(Eval('certificado'))),
        }, depends=['certificado', 'state'])
    comentario = fields.Text('Comentarios', size=None,
        states={
            'readonly': Not(In(Eval('state'), ['new',])),
        }, depends=['state'])
    numero = fields.Char('Numero')
    asegurado = fields.Many2One('party.party', 'Asegurado')
    suma_asegurada = fields.Numeric('Suma Asegurada',
        digits=(16, Eval('_parent_movimiento', {}).get('currency_digits', 2)))
    prima = fields.Numeric('Prima',
        digits=(16, Eval('_parent_movimiento', {}).get('currency_digits', 2)))
    descripcion = fields.Text('Descripcion', size=None)
    vehiculo = fields.One2Many('corseg.vehiculo.modificacion',
        'modificacion', 'Vehiculo', size=1)
    state = fields.Selection([
            ('new', 'Nuevo'),
            ('confirmado', 'Confirmado'),
        ], 'Estado', required=True, readonly=True)

    @staticmethod
    def default_state():
        return 'new'


class CertificadoInclusion(ModelSQL):
    'Certificado - Inclusion'
    __name__ = 'poliza.certificado-inclusion-poliza.movimiento'
    certificado = fields.Many2One('corseg.poliza.certificado', 'Certificado',
        ondelete='CASCADE', select=True, required=True)
    movimiento = fields.Many2One('corseg.poliza.movimiento', 'Movimiento',
        ondelete='CASCADE', select=True, required=True)


class CertificadoExclusion(ModelSQL):
    'Certificado - Exclusion'
    __name__ = 'poliza.certificado-exclusion-poliza.movimiento'
    certificado = fields.Many2One('corseg.poliza.certificado', 'Certificado',
        ondelete='CASCADE', select=True, required=True)
    movimiento = fields.Many2One('corseg.poliza.movimiento', 'Movimiento',
        ondelete='CASCADE', select=True, required=True)


class ExtendidoInclusion(ModelSQL):
    'Extendido - Inclusion'
    __name__ = 'poliza.certificado-inclusion-certificado.extendido'
    extendido = fields.Many2One('corseg.poliza.certificado.extension',
        'Extendido', ondelete='CASCADE', select=True, required=True)
    modificacion = fields.Many2One('corseg.poliza.certificado.modificacion',
        'Movimiento', ondelete='CASCADE', select=True, required=True)


class ExtendidoExclusion(ModelSQL):
    'Extendido - Exclusion'
    __name__ = 'poliza.certificado-exclusion-certificado.extendido'
    extendido = fields.Many2One('corseg.poliza.certificado.extension',
        'Extendido', ondelete='CASCADE', select=True, required=True)
    modificacion = fields.Many2One('corseg.poliza.certificado.modificacion',
        'Movimiento', ondelete='CASCADE', select=True, required=True)
