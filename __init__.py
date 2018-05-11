# This file is part of trytond-corseg module.
# The COPYRIGHT file at the top level of this repository
# contains the full copyright notices and license terms.

from trytond.pool import Pool
from .corseg import *


def register():
    Pool.register(
        CiaSeguros,
        Ramo,
        CiaPoliza,
        Poliza,
        Vendedor,
        TipoComision,
        TablaComisionVendedor,
        TablaComisionEmpresa,
        FormaPago,
        FrecuenciaPago,
        Emision,
        module='corseg', type_='model')
