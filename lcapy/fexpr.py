from __future__ import division
from .fourier import inverse_fourier_transform
from .sfwexpr import sfwExpr
from .sym import fsym, ssym, tsym
#import .texpr as texpr

class fExpr(sfwExpr):

    """Fourier domain expression or symbol."""

    var = fsym
    domain_name = 'Frequency'
    domain_units = 'Hz'

    def __init__(self, val, **assumptions):

        assumptions['real'] = True
        super(fExpr, self).__init__(val, **assumptions)
        # Define when class defined.
        self._fourier_conjugate_class = tExpr

        if self.expr.find(ssym) != set():
            raise ValueError(
                'f-domain expression %s cannot depend on s' % self.expr)
        if self.expr.find(tsym) != set():
            raise ValueError(
                'f-domain expression %s cannot depend on t' % self.expr)

    def inverse_fourier(self):
        """Attempt inverse Fourier transform."""

        result = inverse_fourier_transform(self.expr, self.var, tsym)
        if hasattr(self, '_fourier_conjugate_class'):
            result = self._fourier_conjugate_class(result)
        else:
            result = tExpr(result)
        return result

    def time(self, **assumptions):
        return self.inverse_fourier()
    
    def laplace(self, **assumptions):
        """Determine one-side Laplace transform with 0- as the lower limit."""

        return self.time(**assumptions).laplace()
    
    def plot(self, fvector=None, **kwargs):
        """Plot frequency response at values specified by fvector.

        There are many plotting options, see matplotlib.pyplot.plot.

        For example:
            V.plot(fvector, log_frequency=True)
            V.real.plot(fvector, color='black')
            V.phase.plot(fvector, color='black', linestyle='--')

        By default complex data is plotted as separate plots of magnitude (dB)
        and phase.
        """

        from .plot import plot_frequency
        return plot_frequency(self, fvector, **kwargs)


class Yf(fExpr):

    """f-domain admittance"""

    quantity = 'Admittance'
    units = 'siemens'

    def __init__(self, val, **assumptions):

        super(Yf, self).__init__(val, **assumptions)
        self._fourier_conjugate_class = Yt


class Zf(fExpr):

    """f-domain impedance"""

    quantity = 'Impedance'
    units = 'ohms'

    def __init__(self, val, **assumptions):

        super(Zf, self).__init__(val, **assumptions)
        self._fourier_conjugate_class = Zt


class Hf(fExpr):

    """f-domain transfer function response."""

    quantity = 'Transfer function'
    units = ''

    def __init__(self, val, **assumptions):

        super(Hf, self).__init__(val, **assumptions)
        self._fourier_conjugate_class = Ht


class Vf(fExpr):

    """f-domain voltage (units V/Hz)."""

    quantity = 'Voltage spectrum'
    units = 'V/Hz'

    def __init__(self, val, **assumptions):

        super(Vf, self).__init__(val, **assumptions)
        self._fourier_conjugate_class = Vt


class If(fExpr):

    """f-domain current (units A/Hz)."""

    quantity = 'Current spectrum'
    units = 'A/Hz'

    def __init__(self, val, **assumptions):

        super(If, self).__init__(val, **assumptions)
        self._fourier_conjugate_class = It

from .texpr import Ht, It, Vt, Yt, Zt, tExpr
f = fExpr('f')
