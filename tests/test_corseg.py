# This file is part of tryton-corseg module. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import unittest
import datetime
from decimal import Decimal
import trytond.tests.test_tryton
from trytond.pool import Pool
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.modules.company.tests import create_company, set_company
from trytond.exceptions import UserError


class CorsegTestCase(ModuleTestCase):
    'Test corseg module'
    module = 'corseg'

    @with_transaction()
    def test_corseg(self):
        pool = Pool()
        Certificado = pool.get('corseg.poliza.certificado')
        Extension = pool.get('corseg.poliza.certificado.extension')
        Movimiento = pool.get('corseg.poliza.movimiento')
        CertificadoModificacion = pool.get('corseg.poliza.certificado.modificacion')
        VehiculoTipo = pool.get('corseg.vehiculo.tipo')
        VehiculoMarca = pool.get('corseg.vehiculo.marca')
        VehiculoModelo = pool.get('corseg.vehiculo.modelo')
        Vehiculo = pool.get('corseg.vehiculo')
        ComisionPolizaCia = pool.get('corseg.comision.poliza.cia')
        ComisionMovimientoCia = pool.get('corseg.comision.movimiento.cia')
        ComisionMovimientoVendedor = pool.get('corseg.comision.movimiento.vendedor')
        CiaProductoComisiones = pool.get('corseg.comisiones.cia.producto')
        ComisionAjusteCia = pool.get('corseg.comision.ajuste.cia')
        ComisionAjusteCiaCompensacion = pool.get('corseg.comision.ajuste.cia.compensacion')
        ComisionAjusteVendedor = pool.get('corseg.comision.ajuste.vendedor')

        company = create_company()
        with set_company(company):
            self._set_config(company)
            producto, vendedor, forma_pago, frecuencia_pago = \
                self._get_varios()
            self._movimientos(
                producto, vendedor, forma_pago, frecuencia_pago)
            self._pagos(
                producto, vendedor, forma_pago, frecuencia_pago)
            self._comisiones(
                producto, vendedor, forma_pago, frecuencia_pago)

    def _comisiones(self, producto, vendedor, forma_pago, frecuencia_pago):
        pool = Pool()
        Comision = pool.get('corseg.comision')
        ComisionLinea = pool.get('corseg.comision.linea')
        ComisionVendedor = pool.get('corseg.comision.vendedor')
        ComisionVendedorLinea = pool.get('corseg.comision.vendedor.linea')
        Movimiento = pool.get('corseg.poliza.movimiento')
        Vendedor = pool.get('corseg.vendedor')

        poliza = self._get_poliza("P3", producto)
        fecha = datetime.date.today()

        # Iniciamos la poliza
        mov = self._get_mov_ini(fecha, poliza,
            self._create_party("Contratante P3 Party"),
            vendedor, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        tipo_comision_5 = self._crear_tipo_comision('5.0')
        tipo_comision_10 = self._crear_tipo_comision('10.0')
        tipo_comision_15 = self._crear_tipo_comision('15.0')
        tipo_comision_20 = self._crear_tipo_comision('20.0')
        tipo_comision_35 = self._crear_tipo_comision('35.0')

        comision_5 = Comision(
                name='Basico 5',
                lineas=[
                    ComisionLinea(
                        renovacion=0,
                        tipo_comision=tipo_comision_5,
                        re_renovacion=True,
                        re_cuota=True
                    )
                ]
            )
        comision_5.save()
        comision_10 = Comision(
                name='Basico 10',
                lineas=[
                    ComisionLinea(
                        renovacion=0,
                        tipo_comision=tipo_comision_10,
                        re_renovacion=True,
                        re_cuota=True
                    )
                ]                
            )
        comision_10.save()
        self.assertEqual(len(comision_10.lineas), 1)
        comision_20 = Comision(
                name='Basico 20',
                lineas=[
                    ComisionLinea(
                        renovacion=1, # Se apliza a partir de la renovacion 1
                        tipo_comision=tipo_comision_20,
                        re_renovacion=True,
                        re_cuota=True
                    )
                ]
            )
        comision_20.save()

        # Asignamos los planes de comision al producto
        producto.comision_cia = comision_10
        producto.comision_vendedor_defecto = comision_10
        producto.save()

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto() # Para que calcula las comisiones
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('10.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('1.0'))
        pago.confirmar([pago])

        # Creamos un plan especifico para el vendedor
        comision_vendedor = ComisionVendedor(
                name="Comision Vendedor 5",
                lineas=[
                    ComisionVendedorLinea(
                        vendedor=vendedor,
                        comision=comision_5
                    )
                ],
            )

        producto.comision_vendedor = comision_vendedor
        producto.save()

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('10.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.5'))
        pago.confirmar([pago])

        # Creamos un movimiento que cambie el vendedor,
        # al crear un nuevo pago este volvera a usar el plan 
        # de comision_vendedor_defecto
        new_vendedor = Vendedor(
            party=self._create_party("Nuevo Vendedor Party"))
        vendedor.save()

        mov = Movimiento(
            fecha=fecha,
            poliza=poliza,
            descripcion="Cambio de Vendedor",
            tipo="general",
            vendedor = new_vendedor,
        )
        mov.save()
        Movimiento.procesar([mov])
        Movimiento.confirmar([mov])

        pago = self._create_pago(poliza, new_vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('10.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('1.0'))
        pago.confirmar([pago])

        # Agregamos al nuevo vendedor al plan de comision vendedor,
        # sin embargo crearemos una regla para la renovacion 1,
        # como la renovacion actual es 0, no se podra encontrar la linea
        # y por lo tanto la comision sera 'cero'.
        linea = ComisionVendedorLinea(
                parent=comision_vendedor,
                vendedor=new_vendedor,
                comision=comision_20
            )
        linea.save()

        pago = self._create_pago(poliza, new_vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('10.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.0'))
        pago.confirmar([pago])

        # Creamos una nueva renovacion (1) lo cual
        # hara que se aplique la comision_20 al pago
        mov = self._get_mov_renovacion(fecha, poliza, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        pago = self._create_pago(poliza, new_vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.renovacion, 1)
        self.assertEqual(pago.comision_cia_liq, Decimal('10.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('2.0'))
        pago.confirmar([pago])

        ################################################

        # Un plan mas complejo
        #  Renovacion 0 - 35%
        #  Renovacion 1 - 15%
        #  Renovacion 2 - 5% recurrente
        #  Renovacion 9 - 10% no recurrente en renovacion

        comision_complex = Comision(
                name='Comision COmplex',
                lineas=[
                    ComisionLinea(
                        renovacion=0,
                        tipo_comision=tipo_comision_35,
                        re_renovacion=True,
                        re_cuota=True),
                    ComisionLinea(
                        renovacion=1,
                        tipo_comision=tipo_comision_15,
                        re_renovacion=True,
                        re_cuota=True),
                    ComisionLinea(
                        renovacion=2,
                        tipo_comision=tipo_comision_5,
                        re_renovacion=True,
                        re_cuota=True),
                    ComisionLinea(
                        renovacion=9,
                        tipo_comision=tipo_comision_10,
                        re_renovacion=False,
                        re_cuota=True),
                ]
            )
        comision_complex.save()

        # Asignamos el nuevo plan al producto
        # Usa la comision vendedor de 5%
        producto.comision_cia = comision_complex
        producto.save()

        poliza = self._get_poliza("P4", producto)

        # Iniciamos la poliza
        mov = self._get_mov_ini(fecha, poliza,
            self._create_party("Contratante P4 Party"),
            vendedor, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        # Pago en renovacion 0
        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('35.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('1.75'))
        pago.confirmar([pago])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('10.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('3.5'))
        # redondea el 0.175 a 0.18 por currency_digits=2
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.18'))
        pago.confirmar([pago])

        # Renovacion 1
        mov = self._get_mov_renovacion(fecha, poliza, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('15.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.75'))
        pago.confirmar([pago])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('10.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('1.5'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.08'))
        pago.confirmar([pago])

        # Renovacion 2
        mov = self._get_mov_renovacion(fecha, poliza, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('5.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.25'))
        pago.confirmar([pago])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('10.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('0.5'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.02'))
        pago.confirmar([pago])

        # Renovacion 3 = 2 ya que es recurrente en renovaciones
        mov = self._get_mov_renovacion(fecha, poliza, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('5.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.25'))
        pago.confirmar([pago])

        # Renovacion 8 = 2 ya que es recurrente en renovaciones
        i = 1
        while i < 6:
            mov = self._get_mov_renovacion(fecha, poliza, forma_pago, frecuencia_pago)
            mov.procesar([mov])
            mov.confirmar([mov])
            i += 1
        self.assertEqual(poliza.renovacion, 8)
        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('5.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.25'))
        pago.confirmar([pago])

        # Renovacion 9 10%
        mov = self._get_mov_renovacion(fecha, poliza, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('10.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.5'))
        pago.confirmar([pago])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('10.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('1.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.05'))
        pago.confirmar([pago])

        # Renovacion 10 = 0, ya que no hay linea definida para
        # esta renovacion y la ultima linea no es recurrente en renovacion
        mov = self._get_mov_renovacion(fecha, poliza, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('0.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.0'))
        pago.confirmar([pago])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('10.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('0.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.0'))
        pago.confirmar([pago])

        # Renovacion 11, solo para confirmar
        mov = self._get_mov_renovacion(fecha, poliza, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        pago = self._create_pago(poliza, vendedor, fecha, Decimal('100.0'))
        pago.on_change_monto()
        pago.procesar([pago])
        self.assertEqual(pago.comision_cia_liq, Decimal('0.0'))
        self.assertEqual(pago.comision_vendedor_liq, Decimal('0.0'))
        pago.confirmar([pago])

    def _crear_tipo_comision(self, monto_comision):
        TipoComision = Pool().get('corseg.tipo_comision')
        tipo_comision = TipoComision(
                name="Porcentaje " + str(monto_comision),
                tipo='porcentaje',
                monto=Decimal(monto_comision)
            )
        tipo_comision.save()
        return tipo_comision

    def _pagos(self, producto, vendedor, forma_pago, frecuencia_pago):
        pool = Pool()
        Pago = pool.get('corseg.poliza.pago')

        poliza = self._get_poliza("P2", producto)
        fecha = datetime.date.today()

        mov = self._get_mov_ini(fecha, poliza,
            self._create_party("Contratante P2 Party"),
            vendedor, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        self.assertEqual(poliza.monto_pago, Decimal('0.0'))
        self.assertEqual(poliza.saldo, poliza.prima) # 200.0

        monto_pago = Decimal('15.0')
        pago = self._create_pago(poliza, vendedor, fecha, monto_pago)
        Pago.procesar([pago])
        self.assertEqual(poliza.monto_pago, Decimal('0.0'))
        Pago.confirmar([pago])
        self.assertEqual(pago.state, 'confirmado')
        self.assertEqual(pago.renovacion, 0)
        self.assertEqual(poliza.monto_pago, monto_pago)
        self.assertEqual(poliza.saldo, poliza.prima - monto_pago)

        monto_pago = Decimal('25.0')
        pago = self._create_pago(poliza, vendedor, fecha, monto_pago)
        Pago.procesar([pago])
        Pago.confirmar([pago])
        self.assertEqual(poliza.monto_pago, Decimal('40.0'))
        self.assertEqual(poliza.saldo, poliza.prima - Decimal('40.0'))

        # Renovacion
        mov = self._get_mov_renovacion(
                fecha, poliza, forma_pago, frecuencia_pago)
        mov.procesar([mov])
        mov.confirmar([mov])

        # Se arrastra como saldo negativo de la renovacion anterior
        self.assertEqual(poliza.monto_pago, Decimal('-160.0'))

        monto_pago = Decimal('15.0')
        pago = self._create_pago(poliza, vendedor, fecha, monto_pago)
        Pago.procesar([pago])
        Pago.confirmar([pago])
        self.assertEqual(pago.renovacion, 1)
        self.assertEqual(poliza.monto_pago, Decimal('-145.0'))
        self.assertEqual(poliza.saldo, Decimal('250.0') - Decimal('-145.0'))

    def _create_pago(self, poliza, vendedor, fecha, monto):
        pool = Pool()
        Pago = pool.get('corseg.poliza.pago')

        pago = Pago(
                poliza=poliza,
                fecha=fecha,
                monto=monto,
            )
        pago.on_change_poliza()
        pago.save()
        return pago

    def _movimientos(self, producto, vendedor, forma_pago, frecuencia_pago):
        pool = Pool()
        Movimiento = pool.get('corseg.poliza.movimiento')

        poliza = self._get_poliza("P1", producto)
        fecha = datetime.date.today()

        mov = Movimiento()
        with self.assertRaises(UserError):
            # El primer movimiento debe ser del tipo iniciacion
            mov.fecha = fecha
            mov.poliza = poliza
            mov.descripcion = "Test"
            mov.tipo = "general"
            mov.save()
            Movimiento.procesar([mov])
        Movimiento.delete([mov])

        mov = self._get_mov_ini(fecha, poliza,
            self._create_party("Contratante Party"),
            vendedor, forma_pago, frecuencia_pago)
        Movimiento.procesar([mov])
        self.assertEqual(mov.state, 'procesado')
        Movimiento.confirmar([mov])
        self.assertEqual(mov.renovacion, 0)
        self.assertEqual(mov.state, 'confirmado')
        self.assertEqual(poliza.state, 'vigente')
        self.assertEqual(poliza.renovacion, 0)
        self.assertEqual(poliza.no_cuotas, 10)
        self.assertEqual(poliza.monto_pago, Decimal('0.0'))
        self.assertEqual(poliza.saldo, poliza.prima) # 200.0

        # Modificacion simple
        mov = Movimiento(
            fecha=fecha,
            poliza=poliza,
            descripcion="Modificacion Simple",
            tipo="general",
            no_cuotas=11,
        )
        mov.save()
        Movimiento.procesar([mov])
        self.assertEqual(poliza.no_cuotas, 10)
        # La poliza se modifica solo al confirmar el movimiento
        Movimiento.confirmar([mov])
        self.assertEqual(poliza.no_cuotas, 11)
        # No varia la prima de la poliza
        self.assertEqual(poliza.prima, Decimal('200.0'))

        # Modificacion ajuste de prima a la baja
        mov = Movimiento(
            fecha=fecha,
            poliza=poliza,
            descripcion="Modificacion Simple a la baja",
            tipo="general",
            prima=-Decimal('50.0'),
        )
        mov.save()
        Movimiento.procesar([mov])
        Movimiento.confirmar([mov])
        self.assertEqual(poliza.prima, Decimal('150.0'))

        # Renovacion
        mov = self._get_mov_renovacion(
                fecha, poliza, forma_pago, frecuencia_pago)
        Movimiento.procesar([mov])
        Movimiento.confirmar([mov])
        self.assertEqual(mov.renovacion, 1)
        self.assertEqual(poliza.state, 'vigente')
        self.assertEqual(poliza.renovacion, 1)
        self.assertEqual(poliza.no_cuotas, 10)
        self.assertEqual(poliza.monto_pago, Decimal('-150.0'))
        self.assertEqual(poliza.prima, Decimal('250.0'))
        # Se suman la prima de la renovacion anterior con esta
        self.assertEqual(poliza.saldo, Decimal('400.0'))

        # Cancelacion
        mov = Movimiento(
            fecha=fecha,
            poliza=poliza,
            descripcion="Cancelacion",
            tipo="endoso",
            tipo_endoso="cancelacion",
        )
        mov.save()
        Movimiento.procesar([mov])
        Movimiento.confirmar([mov])
        self.assertEqual(mov.state, 'confirmado')
        self.assertEqual(poliza.state, 'cancelada')

    def _get_mov_ini(self, fecha, poliza, contratante,
                vendedor, forma_pago, frecuencia_pago):
        pool = Pool()
        Movimiento = pool.get('corseg.poliza.movimiento')

        mov = Movimiento(
            fecha=fecha,
            poliza=poliza,
            descripcion="Movimiento Iniciacion",
            tipo="endoso",
            tipo_endoso="iniciacion",
            contratante=contratante,
            f_emision=fecha,
            f_desde=fecha,
            f_hasta=fecha,
            suma_asegurada=Decimal('15000.0'),
            prima=Decimal('200.0'),
            vendedor=vendedor,
            forma_pago=forma_pago,
            frecuencia_pago=frecuencia_pago,
            no_cuotas=10,
        )
        mov.save()
        return mov

    def _get_mov_renovacion(self, fecha, poliza, forma_pago, frecuencia_pago):
        pool = Pool()
        Movimiento = pool.get('corseg.poliza.movimiento')

        mov = Movimiento(
            fecha=fecha,
            poliza=poliza,
            descripcion="Movimiento Renovacion",
            tipo="endoso",
            tipo_endoso="renovacion",
            f_emision=fecha,
            f_desde=fecha,
            f_hasta=fecha,
            suma_asegurada=Decimal('20000.0'),
            prima=Decimal('250.0'),
            forma_pago=forma_pago,
            frecuencia_pago=frecuencia_pago,
            no_cuotas=10,
        )
        mov.save()
        return mov

    def _get_poliza(self, numero, producto):
        pool = Pool()
        Poliza = pool.get('corseg.poliza')
        GrupoPoliza = pool.get('corseg.poliza.grupo')
        OrigenPoliza = pool.get('corseg.poliza.origen')
        ComentarioPoliza = pool.get('corseg.poliza.comentario')

        poliza = Poliza(
                cia=producto.cia,
                cia_producto=producto,
                numero=numero,                
            )
        poliza.save()
        return poliza

    def _get_varios(self):
        pool = Pool()
        Ramo = pool.get('corseg.ramo')
        CiaSeguros = pool.get('corseg.cia')
        CiaProducto = pool.get('corseg.cia.producto')
        Vendedor = pool.get('corseg.vendedor')
        FormaPago = pool.get('corseg.forma_pago')
        FrecuenciaPago = pool.get('corseg.frecuencia_pago')

        ramo = Ramo(name="Automovil")
        ramo.save()

        cia = CiaSeguros(
            name="Cia de Seguros", party=self._create_party("Cia Party"))
        cia.save()

        producto=CiaProducto(
                name="Automovil Producto",
                cia=cia,
                ramo=ramo,
            )
        producto.save()

        vendedor = Vendedor(
            party=self._create_party("Vendedor Party"))
        vendedor.save()

        forma_pago = FormaPago(name="ACH")
        forma_pago.save()

        frecuencia_pago = FrecuenciaPago(name="Mensual", meses=1)
        frecuencia_pago.save()
        return producto, vendedor, forma_pago, frecuencia_pago

    def _set_config(self, company):
        Config = Pool().get('corseg.configuration')
        config = Config(
                pago_seq=self._get_sequence('Poliza Pago',
                    'corseg.pago', 'PG-', company),
                movimiento_seq=self._get_sequence('Poliza Movimiento',
                    'corseg.movimiento', 'MV-', company),
                liq_cia_seq=self._get_sequence('Liquidacion Comision Cia',
                    'corseg.liquidacion.cia', 'LQC-', company),
                liq_vendedor_seq=self._get_sequence('Liquidacion Comision Vendedor',
                    'corseg.liquidacion.vendedor', 'LQV-', company),
                ajuste_comision_cia_seq=self._get_sequence('Comision Ajuste Cia',
                    'corseg.comision.ajuste.cia', 'AJC-', company),
                ajuste_comision_vendedor_seq = self._get_sequence('Comision Ajuste Vendedor',
                    'corseg.comision.ajuste.vendedor', 'AJV-', company)
            )
        config.save()

    def _get_sequence(
            self, name, code, prefix, company, is_strict=False):
        if is_strict:
            obj_sequence = Pool().get('ir.sequence.strict')
        else:
            obj_sequence = Pool().get('ir.sequence')

        seq = obj_sequence()
        seq.name = name
        seq.code = code
        seq.padding = 6
        seq.company = company
        seq.prefix = prefix
        seq.type = 'incremental'
        seq.save()
        return seq

    def _create_party(self, name):
        Party = Pool().get('party.party')
        party = Party(
                name=name,
            )
        return party

def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        CorsegTestCase))
    return suite
