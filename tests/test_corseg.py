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
        
        Asegurado = pool.get('corseg.poliza.asegurado')
        Beneficiario = pool.get('corseg.poliza.beneficiario')
        Certificado = pool.get('corseg.poliza.certificado')
        CiaProducto = pool.get('corseg.cia.producto')
        CiaSeguros = pool.get('corseg.cia')
        ComisionCia = pool.get('corseg.comision.cia')
        ComisionCiaDetalle = pool.get('corseg.comision.cia.detalle')
        ComisionVendedor = pool.get('corseg.comision.vendedor')
        ComisionVendedorDetalle = pool.get('corseg.comision.vendedor.detalle')
        FormaPago = pool.get('corseg.forma_pago')
        FrecuenciaPago = pool.get('corseg.frecuencia_pago')
        GrupoPoliza = pool.get('corseg.poliza.grupo')
        Movimiento = pool.get('corseg.poliza.movimiento')
        Poliza = pool.get('corseg.poliza')
        Ramo = pool.get('corseg.ramo')
        TipoComision = pool.get('corseg.tipo_comision')
        VehiculoMarca = pool.get('corseg.vehiculo.marca')
        VehiculoModelo = pool.get('corseg.vehiculo.modelo')
        Vendedor = pool.get('corseg.vendedor')

        # TODO Multivalue para tipo comision en corseg.cia.poliza


def suite():
    suite = trytond.tests.test_tryton.suite()
    suite.addTests(unittest.TestLoader().loadTestsFromTestCase(
        CorsegTestCase))
    return suite
