# This file is part of Tryton. The COPYRIGHT file at the top level of
# this repository contains the full copyright notices and license terms.

try:
    from trytond.modules.corseg.tests.test_corseg import suite
except ImportError:
    from .test_corseg import suite


__all__ = ['suite']
