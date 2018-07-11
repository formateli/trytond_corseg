# This file is part of tryton-corseg module. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

import unittest
import trytond.tests.test_tryton
from trytond.tests.test_tryton import ModuleTestCase, with_transaction
from trytond.pool import Pool


class CorsegTestCase(ModuleTestCase):
    'Test corseg module'
    module = 'corseg'

    @with_transaction()
    def test_corseg(self):
        pool = Pool()

        Ramo = pool.get('corseg.ramo')
        CiaSeguros = pool.get('corseg.cia')
        CiaProducto = pool.get('corseg.cia.producto')
        GrupoPoliza = pool.get('corseg.poliza.grupo')
        OrigenPoliza = pool.get('corseg.poliza.origen')
        ComentarioPoliza = pool.get('corseg.poliza.comentario')
        Poliza = pool.get('corseg.poliza')
        Vendedor = pool.get('corseg.vendedor')
        Certificado = pool.get('corseg.poliza.certificado')
        Extension = pool.get('corseg.poliza.certificado.extension')
        Movimiento = pool.get('corseg.poliza.movimiento')
        CertificadoModificacion = pool.get('corseg.poliza.certificado.modificacion')
        FormaPago = pool.get('corseg.forma_pago')
        FrecuenciaPago = pool.get('corseg.frecuencia_pago')
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

        company = self._create_company()


    def _create_company(self):
        Company = Pool().get('company.company')
        company = Company(
                name="Test Company",
                party=self._create_party('Test Party')
            )
        return company

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
