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
        Pago = pool.get('corseg.poliza.pago')
        VehiculoTipo = pool.get('corseg.vehiculo.tipo')
        VehiculoMarca = pool.get('corseg.vehiculo.marca')
        VehiculoModelo = pool.get('corseg.vehiculo.modelo')
        Vehiculo = pool.get('corseg.vehiculo')
        TipoComision = pool.get('corseg.tipo_comision')
        Comision = pool.get('corseg.comision')
        ComisionLinea = pool.get('corseg.comision.linea')
        ComisionVendedor = pool.get('corseg.comision.vendedor')
        ComisionVendedorLinea = pool.get('corseg.comision.vendedor.linea')
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
            poliza, vendedor, forma_pago, frecuencia_pago = \
                self._get_poliza()
            self._movimiento_ini(
                poliza, vendedor, forma_pago, frecuencia_pago)
            
    def _movimiento_ini(self, poliza, vendedor, forma_pago, frecuencia_pago):
        pool = Pool()
        Movimiento = pool.get('corseg.poliza.movimiento')

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

        # Iniciacion
        mov = Movimiento(
            fecha=fecha,
            poliza=poliza,
            descripcion="Movimiento Iniciacion",
            tipo="endoso",
            tipo_endoso="iniciacion",
            contratante=self._create_party("Contratante Party"),
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
        Movimiento.procesar([mov])
        self.assertEqual(mov.state, 'procesado')
        Movimiento.confirmar([mov])
        self.assertEqual(mov.renovacion, 0)
        self.assertEqual(mov.state, 'confirmado')

    def _get_poliza(self):
        pool = Pool()
        Ramo = pool.get('corseg.ramo')
        CiaSeguros = pool.get('corseg.cia')
        CiaProducto = pool.get('corseg.cia.producto')
        Poliza = pool.get('corseg.poliza')
        Vendedor = pool.get('corseg.vendedor')
        FormaPago = pool.get('corseg.forma_pago')
        FrecuenciaPago = pool.get('corseg.frecuencia_pago')
        GrupoPoliza = pool.get('corseg.poliza.grupo')
        OrigenPoliza = pool.get('corseg.poliza.origen')
        ComentarioPoliza = pool.get('corseg.poliza.comentario')

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

        poliza = Poliza(
                cia=producto.cia,
                cia_producto=producto,
                numero="P123",                
            )
        poliza.save()

        return poliza, vendedor, forma_pago, frecuencia_pago

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
