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
        CiaSeguros = pool.get('corseg.cia')
        Ramo = pool.get('corseg.ramo')
        CiaPoliza = pool.get('corseg.cia.poliza')
        Poliza = pool.get('corseg.poliza')
        Vendedor = pool.get('corseg.vendedor')
        TipoComision = pool.get('corseg.tipo_comision')
        TablaComisionVendedor = pool.get('corseg.comision.vendedor')
        FormaPago = pool.get('corseg.forma_pago')
        FrecuenciaPago = pool.get('corseg.frecuencia_pago')
        Emision = pool.get('corseg.emision')
        VehiculoMarca = pool.get('corseg.vehiculo.marca')
        VehiculoModelo = pool.get('corseg.vehiculo.modelo')


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        CorsegTestCase))
    return suite
