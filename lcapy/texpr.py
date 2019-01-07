from __future__ import division
from .expr import Expr
from .functions import sin, cos, exp
from .sym import fsym, ssym, tsym, j, omegasym
from .acdc import ACChecker, is_dc, is_ac, is_causal
from .laplace import laplace_transform
from .fourier import fourier_transform

__all__ = ('Ht', 'It', 'Vt', 'Yt', 'Zt')


class tExpr(Expr):

    """t-domain expression or symbol."""

    var = tsym
    domain_name = 'Time'
    domain_units = 's'

    def __init__(self, val, **assumptions):

        assumptions['real'] = True
        super(tExpr, self).__init__(val, **assumptions)

        self._fourier_conjugate_class = fExpr
        self._laplace_conjugate_class = sExpr

        if self.expr.find(ssym) != set():
            raise ValueError(
                't-domain expression %s cannot depend on s' % self.expr)

    def infer_assumptions(self):

        self.assumptions['dc'] = False
        self.assumptions['ac'] = False
        self.assumptions['causal'] = False

        var = self.var
        if is_dc(self, var):
            self.assumptions['dc'] = True
            return

        if is_ac(self, var):
            self.assumptions['ac'] = True
            return

        if is_causal(self, var):
            self.assumptions['causal'] = True

    def laplace(self):
        """Determine one-side Laplace transform with 0- as the lower limit."""

        # The assumptions are required to help with the inverse Laplace
        # transform is required.
        self.infer_assumptions()
        result = laplace_transform(self.expr, self.var, ssym)

        if hasattr(self, '_laplace_conjugate_class'):
            result = self._laplace_conjugate_class(result, **self.assumptions)
        else:
            result = sExpr(result, **self.assumptions)
        return result

    def fourier(self):
        """Attempt Fourier transform."""

        result = fourier_transform(self.expr, self.var, fsym)

        if hasattr(self, '_fourier_conjugate_class'):
            result = self._fourier_conjugate_class(result, **self.assumptions)
        else:
            result = fExpr(result **self.assumptions)
        return result

    def phasor(self, **assumptions):

        check = ACChecker(self, t)
        if not check.is_ac:
            raise ValueError('Do not know how to convert %s to phasor' % self)
        phasor = Phasor(check.amp * exp(j * check.phase), omega=check.omega)
        return phasor

    def plot(self, t=None, **kwargs):

        from .plot import plot_time
        return plot_time(self, t, **kwargs)

    def sample(self, t):
        """Return a discrete-time signal evaluated at time values specified by
        vector t. """

        return self.evaluate(t)
    

class Yt(tExpr):

    """t-domain 'admittance' value."""

    units = 'siemens/s'

    def __init__(self, val, **assumptions):

        super(Yt, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = Ys
        self._fourier_conjugate_class = Yf


class Zt(tExpr):

    """t-domain 'impedance' value."""

    units = 'ohms/s'

    def __init__(self, val, **assumptions):

        super(Zt, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = Zs
        self._fourier_conjugate_class = Zf


class Vt(tExpr):

    """t-domain voltage (units V)."""

    quantity = 'Voltage'
    units = 'V'

    def __init__(self, val, **assumptions):

        super(Vt, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = Vs
        self._fourier_conjugate_class = Vf


class It(tExpr):

    """t-domain current (units A)."""

    quantity = 'Current'
    units = 'A'

    def __init__(self, val, **assumptions):

        super(It, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = Is
        self._fourier_conjugate_class = If


class Ht(tExpr):

    """impulse response"""

    quantity = 'Impulse response'
    units = '1/s'

    def __init__(self, val, **assumptions):

        super(Ht, self).__init__(val, **assumptions)
        self._laplace_conjugate_class = Hs
        self._fourier_conjugate_class = Hf

from .sexpr import Hs, Is, Vs, Ys, Zs, sExpr
from .fexpr import Hf, If, Vf, Yf, Zf, fExpr
from .phasor import Phasor
t = tExpr('t')

