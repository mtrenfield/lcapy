from __future__ import division
from .expr import Exprdict
from .sym import tsym, omegasym, symbols_find, is_sympy, symsymbol
from .acdc import is_ac
from .printing import pprint, pretty
import six

__all__ = ('Super', 'Vsuper', 'Isuper')

class Super(Exprdict):
    """This class represents a superposition of different signal types:
    DC, AC, transient, and noise.
    
    The time-domain representation is returned with the time method,
    V.time(), or with the notation V(t).  This does not include the
    noise component.

    The Laplace representation is returned with the laplace method,
    V.laplace() or with the notation V(s).  This does not include the
    noise component.

    Noise components with different noise indentifiers are stored
    separately, keyed by the noise identifier.  They are ignored by
    the laplace() and time() methods.

    The total noise can be accessed with the .n attribute.  This sums
    each of the noise components in quadrature since they are
    independent.

    For example, consider V = Vsuper('cos(3 * t) + exp(-4 * t) + 5')

    str(V(t)) gives 'cos(3*t) + 5 + exp(-4*t)'

    str(V(s)) gives 's/(9*(s**2/9 + 1)) + 1/(4*(s/4 + 1)) + 5/s'

    V.dc gives 5

    V.ac gives {3: 1}

    V.s gives 1/(s + 4)
    """

    # TODO: rework this class to better show 0 result.
    
    # Where possible this class represents a signal in the time-domain.
    # It can decompose a signal into AC, DC, and transient components.
    # The 't' key is the transient component viewed in the time domain.
    # The 's' key is the transient component viewed in the Laplace domain.    
    
    def __init__(self, *args, **kwargs):
        super (Super, self).__init__()

        if any(args):
            for arg in args:
                self.add(arg)

    def _representation(self):
        if not any(self):
            return 0
        if False:
            return self
        # It is probably less confusing for a user to display
        # using a decomposition in the transform domains.
        # We could present the result in the time-domain but this
        # hides the underlying way the signal is analysed.
        return self.decompose()
                
    def _repr_pretty_(self, p, cycle):

        p.text(pretty(self._representation()))

    def pprint(self):
        """Pretty print"""

        return pprint(self._representation())

    def __getitem__(self, key):
        # This allows a[omega] to work if omega used as key
        # instead of 'omega'.
        if hasattr(key, 'expr'):
            key = key.expr
        return super(Super, self).__getitem__(key)

    def ac_keys(self):
        """Return list of keys for all ac components."""

        keys = []
        for key in self.decompose().keys():
            if not isinstance(key, str) or key is 'w':
                keys.append(key)
        return keys

    def noise_keys(self):
        """Return list of keys for all noise components."""

        keys = []
        for key in self.keys():
            if isinstance(key, str) and key[0] is 'n':
                keys.append(key)
        return keys    

    def has(self, subexpr):
        """Test whether the sub-expression is contained.  For example,
         V.has(exp(t)) 
         V.has(t)

        """        
        for key,expr  in self.items():
            if expr.has(subexpr):
                return True
        return False

    def has_symbol(self, sym):
        """Test if have symbol.  For example,
        V.has_symbol('a')
        V.has_symbol(t)
        
        """                        
        return self.has(symsymbol(sym))
    
    @property
    def has_dc(self):
        """True if there is a DC component."""                
        return self == 0 or 'dc' in self.decompose()

    @property
    def has_ac(self):
        """True if there is an AC component."""        
        return self.ac_keys() != []

    @property
    def has_s(self):
        """True if have transient component defined in the s-domain."""
        return 's' in self

    @property
    def has_t(self):
        """True if have transient component defined in the time-domain."""        
        return 't' in self

    @property
    def has_transient(self):
        """True if have transient component."""        
        return self.has_s or self.has_t

    @property
    def has_n(self):
        """True if there is a noise component."""                
        return self.noise_keys() != []

    @property
    def is_dc(self):
        """True if only has a DC component."""                
        return self == 0 or (self.has_dc and list(self.decompose().keys()) == ['dc'])

    @property
    def is_ac(self):
        """True if only has AC components."""                        
        return self.has_ac and self.ac_keys() == list(self.keys())

    @property
    def is_n(self):
        """True if only has noise components."""                                
        return self.has_n and self.noise_keys() == list(self.keys())

    @property
    def is_s_transient(self):
        """True if only has s-domain transient component."""
        return list(self.decompose().keys()) == ['s']

    @property
    def is_t_transient(self):
        """True if only has t-domain transient component."""
        return list(self.decompose().keys()) == ['t']    

    @property
    def is_transient(self):
        """True if only has transient component(s).  Note, should
        not have both t and s components."""
        return self.is_s_transient or self.is_t_transient
    
    @property
    def is_causal(self):
        return self.is_transient and self.s.is_causal

    @property
    def is_superposition(self):
        return len(self.keys()) > 1

    def __call__(self, arg, **assumptions):
        """
        arg determines the returned representation
          t: time-domain representation
          s: Laplace domain representation
          f: Fourier representation
          omega: Fourier representation (angular frequency)
          jomega: Laplace domain representation with s = jomega

        For example, V(t), V(f), or V(2 * t).

        If arg is a constant, the time-domain representation
        evaluated at the argument is returned, for example,
        V(0) returns the dc value.
        """

        from .transform import call
        return call(self, arg, **assumptions)        

    def subs(self, *args, **kwargs):

        return self.time().subs(*args, **kwargs)
    
    def transform(self, arg, **assumptions):
        """Transform into a different domain."""        

        from .transform import transform
        return transform(self, arg, **assumptions)

    def __add__(self, x):

        def _is_s_arg(x):
            return isinstance(x, sExpr) or (isinstance(x, Super) and 's' in x)

        if _is_s_arg(x):
            new = self.decompose()
        else:
            new = self.__class__(self)            

        if isinstance(x, Super):
            for value in x.values():
                new.add(value)
        else:
            new.add(x)
        return new

    def __radd__(self, x):
        return self.__add__(x)

    def __sub__(self, x):
        return -x + self

    def __rsub__(self, x):
        return -self + x

    def __neg__(self):
        new = self.__class__()
        for kind, value in self.items():
            new[kind] = -value
        return new

    def __scale__(self, x):
        new = self.__class__()
        for kind, value in self.items():
            new[kind] = value * x
        return new

    def __eq__(self, x):

        # Cannot compare noise by subtraction.
        if isinstance(x, Super):
            # TODO, be smarter about transformations
            x = x.decompose()
            y = self.decompose()            
            if y.items() != x.items():
                return False
            for kind, value in y.items():
                if value != x[kind]:
                    return False
            return True
        
        diff = self - x
        for kind, value in diff.items():
            if value != 0:
                return False
        return True


    def __ne__(self, x):

        # Cannot compare noise by subtraction.
        if isinstance(x, Super):
            # TODO, be smarter about transformations
            x = x.decompose()
            y = self.decompose()            
            if y.items() != x.items():
                return True
            for kind, value in y.items():
                if value != x[kind]:
                    return True
            return False
        
        diff = self - x
        for kind, value in diff.items():
            if value != 0:
                return True
        return False    

    def _decompose(self, expr):
        """Decompose a t-domain expr into AC, DC, and s-domain
        transient components."""

        # Extract DC components
        dc = expr.expr.coeff(tsym, 0)
        if dc != 0:
            self['dc'] = cExpr(dc)
            expr -= dc

        if expr == 0:
            return

        # Extract AC components        
        ac = 0
        terms = expr.expr.as_ordered_terms()
        for term in terms:
            if is_ac(term, tsym):
                self.add(tExpr(term).phasor())
                ac += term

        expr -= ac
        if expr == 0:
            return

        # The remaining components are considered transient
        # so convert to Laplace representation.
        sval = expr.laplace()

        self['s'] = sval

    def decompose(self):
        """Decompose into a new representation in the transform domains."""
        
        if hasattr(self, '_decomposition'):
            return self._decomposition

        new = self.__class__()
        if 't' in self:
            new._decompose(self['t'])
        for kind, value in self.items():
            if kind != 't':
                new.add(value)
        self._decomposition = new                
        return new
    
    def select(self, kind):
        """Select a component of the signal representation by kind where:
        'super' : the entire superposition
        'time' :  the time domain representation (equivalent to self.time())
        'ivp' :  the s-domain representation (equivalent to self.laplace())
        'dc' : the DC component
        omega : the AC component with angular frequency omega
        's' : the transient component in the s-domain
        'n' : the noise component
        't' : the time-domain transient component (this may or may not
              include the DC and AC components).

        """
        if kind is 'super':
            return self
        elif kind is 'time':
            return self.time()
        elif kind is 'ivp':
            return self.laplace()

        if isinstance(kind, str) and kind[0] is 'n':
            if kind not in self:
                return self.decompose_domains['n'](0)
            return self[kind]
        
        obj = self
        if 't' in self and 't' != kind:
            # The rationale here is that there may be
            # DC and AC components included in the 't' part.
            obj = self.decompose()
            
        if kind not in obj:
            if kind not in obj.decompose_domains:
                kind = 'ac'
            return obj.decompose_domains[kind](0)
        return obj[kind]

    def netval(self, kind):

        def kind_keyword(kind):
            if isinstance(kind, str) and kind[0] is 'n':
                return 'noise'
            elif kind is 'ivp':
                return 's'
            elif kind in ('t', 'time'):
                return ''                
            elif not isinstance(kind, str):
                return 'ac'
            return kind

        val = self.select(kind)
        if kind in ('s', 'ivp') and (val.is_causal or val.is_dc or val.is_ac):
            # Convert to time representation so that can re-infer
            # causality, etc.
            return '{%s}' % val.time()

        keyword = kind_keyword(kind)
        
        if 'nid' in val.assumptions:
            return '%s {%s} %s' % (keyword, val, val.nid)

        if keyword is 'ac':
            return '%s {%s} {%s} {%s}' % (keyword, val, 0, val.omega)

        return '%s {%s}' % (keyword, val)
    
    def _kind(self, value):
        if isinstance(value, Phasor):
            # Use angular frequency for key.  This can be a nuisance
            # for numerical values since cannot use x.3 syntax
            # say for an angular frequency of 3.
            key = value.omega
            if hasattr(key, 'expr'):
                key = key.expr
            return key

        for kind, mtype in self.decompose_domains.items():
            if isinstance(value, mtype):
                return kind
        return None

    def _parse(self, string):
        """Parse t or s-domain expression or symbol, interpreted in time
        domain if not containing s, omega, or f.  Return most
        appropriate transform domain.

        """

        symbols = symbols_find(string)

        if 's' in symbols:
            return self.add(sExpr(string))

        if 'omega' in symbols:
            if 't' in symbols:
                # Handle cos(omega * t)
                return self.add(tExpr(string))
            return self.add(omegaExpr(string))

        if 'f' in symbols:
            # TODO, handle AC of different frequency
            return self.add(fExpr(string))

        return self.add(tExpr(string))

    def _add_noise(self, value):

        if value.nid not in self:
            self[value.nid] = value
        else:
            self[value.nid] += value
            if self[value.nid] == 0:
                self.pop(value.nid)
    
    def add(self, value):
        """Add a value into the superposition."""

        # Avoid triggering __eq__ for Super otherwise have infinite recursion
        if not isinstance(value, Super) and value == 0:
            return

        if '_decomposition' in self:
            delattr(self, '_decomposition')

        if isinstance(value, Super):
            for kind, value in value.items():
                self.add(value)
            return

        if isinstance(value, six.string_types):
            return self._parse(value)

        if isinstance(value, noiseExpr):
            self._add_noise(value)
            return
        
        # DC should be real but allow const complex value.
        if isinstance(value, (int, float, complex)):
            value = self.decompose_domains['dc'](value)
        elif is_sympy(value):
            try:
                # Look for I, 5 * I, etc.
                if value.is_constant:
                    value = self.decompose_domains['dc'](value)
            except:
                pass

        kind = self._kind(value)
        if kind is None:
            if value.__class__ in self.type_map:
                value = self.type_map[value.__class__](value)
            else:
                for cls1, cls2 in self.type_map.items():
                    if isinstance(value, cls1):
                        value = cls2(value)
                        break
            kind = self._kind(value)

        if kind is None:
            raise ValueError('Cannot handle value %s of type %s' %
                             (value, type(value).__name__))

        if kind not in self:
            self[kind] = value
        else:
            self[kind] += value

    @property
    def dc(self):
        """Return the DC component."""        
        return self.select('dc')

    @property
    def ac(self):
        """Return the AC components."""                
        if 't' in self.keys():
            self = self.decompose()        
        return Exprdict({k: v for k, v in self.items() if k in self.ac_keys()})

    @property
    def s(self):
        """Return the s-domain representation of the transient component.
        This is not the full s-domain representation as returned by the
        laplace method V.laplace() or V(s).

        This attribute may be deprecated due to possible confusion."""
        return self.select('s')

    @property
    def n(self):
        result = self.decompose_domains['n'](0)
        for key in self.noise_keys():
            result += self[key]
        return result

    @property
    def noise(self):
        """Return the total noise."""
        return self.n

    @property
    def w(self):
        """Return the AC component with angular frequency omega."""        
        return self.select(omegasym)    

    def time(self, **assumptions):
        """Convert to time domain."""

        result = self.time_class(0)

        # TODO, integrate noise
        for val in self.values():
            if hasattr(val, 'time'):
                result += val.time(**assumptions)
            else:
                result += val
        return result

    def transient_response(self, tvector=None):
        """Evaluate transient (impulse) response."""

        texpr = self.time()

        if tvector is None:
            return texpr

        return texpr.evaluate(tvector)
    
    def frequency_response(self, fvector=None):
        """Convert to frequency domain and evaluate response if frequency
        vector specified.

        """

        X = self.fourier()

        if fvector is None:
            return X

        return X.evaluate(fvector)

    def laplace(self, **assumptions):
        """Convert to s-domain."""                

        result = self.laplace_class(0)
        for val in self.values():
            result += val.laplace()
        return result

    def fourier(self, **assumptions):
        """Convert to Fourier domain."""        

        # TODO, could optimise.
        return self.time(**assumptions).fourier(**assumptions)

    def canonical(self):
        new = self.__class__()
        for kind, value in self.items():
            new[kind] = value.canonical()

        return new

    def simplify(self):
        new = self.__class__()
        for kind, value in self.items():
            new[kind] = value.simplify()

        return new


class Vsuper(Super):

    def __init__(self, *args, **kwargs):
        self.type_map = {cExpr: Vconst, sExpr : Vs, noiseExpr: Vn,
                         omegaExpr: Vphasor, tExpr : Vt}
        self.decompose_domains = {'s': Vs, 'ac': Vphasor, 'dc':
                                  Vconst, 'n': Vn, 't': Vt}
        self.time_class = Vt
        self.laplace_class = Vs    

        super (Vsuper, self).__init__(*args, **kwargs)
        
    def __rmul__(self, x):
        return self.__mul__(x)

    def __mul__(self, x):
        if isinstance(x, (int, float)):
            return self.__scale__(x)

        if isinstance(x, Super):
            raise TypeError('Cannot multiply types %s and %s. '
            'You need to extract a specific component, e.g., a.s * b.s' %
            (type(self).__name__, type(x).__name__))

        if not isinstance(x, Ys):
            raise TypeError("Unsupported types for *: 'Vsuper' and '%s'" %
                            type(x).__name__)
        obj = self
        if x.has(s):
            obj = self.decompose()
        
        new = Isuper()
        if 'dc' in obj:
            # TODO, fix types
            new += Iconst(obj['dc'] * cExpr(x.jomega(0)))
        for key in obj.ac_keys():
            new += obj[key] * x.jomega(obj[key].omega)
        for key in obj.noise_keys():            
            new += obj[key] * x.jomega
        if 's' in obj:
            new += obj['s'] * x
        if 't' in obj:
            new += self['t'] * tExpr(x)
            
        return new

    def __div__(self, x):
        if isinstance(x, (int, float)):
            return self.__scale__(1 / x)

        if isinstance(x, Super):
            raise TypeError("""
Cannot divide types %s and %s.  You need to extract a specific component, e.g., a.s / b.s.  If you want a transfer function use a.laplace() / b.laplace()""" % (type(self).__name__, type(x).__name__))

        if not isinstance(x, Zs):
            raise TypeError("Unsupported types for /: 'Vsuper' and '%s'" %
                            type(x).__name__)
        return self * Ys(1 / x)

    def __truediv__(self, x):
        return self.__div__(x)

    def cpt(self):
        from .oneport import V
        # Perhaps should generate more specific components such as Vdc?
        return V(self.time())

class Isuper(Super):

    def __init__(self, *args, **kwargs):    

        self.type_map = {cExpr: Iconst, sExpr : Is, noiseExpr: In,
                         omegaExpr: Iphasor, tExpr : It}
        self.decompose_domains = {'s': Is, 'ac': Iphasor, 'dc':
                                  Iconst, 'n': In, 't': It}
        self.time_class = It
        self.laplace_class = Is

        super (Isuper, self).__init__(*args, **kwargs)

    def __rmul__(self, x):
        return self.__mul__(x)
    
    def __mul__(self, x):
        if isinstance(x, (int, float)):
            return self.__scale__(x)

        if isinstance(x, Super):
            raise TypeError('Cannot multiply types %s and %s. '
            'You need to extract a specific component, e.g., a.s * b.s' %
            (type(self).__name__, type(x).__name__))
        
        if not isinstance(x, Zs):
            raise TypeError("Unsupported types for *: 'Isuper' and '%s'" %
                            type(x).__name__)
        obj = self
        if x.has(s):
            obj = self.decompose()

        new = Vsuper()
        if 'dc' in obj:
            # TODO, fix types
            new += Vconst(obj['dc'] * cExpr(x.jomega(0)))
        for key in obj.ac_keys():
            new += obj[key] * x.jomega(obj[key].omega)
        for key in obj.noise_keys():            
            new += obj[key] * x.jomega            
        if 's' in obj:
            new += obj['s'] * x
        if 't' in obj:
            new += obj['t'] * tExpr(x)                        
        return new

    def __div__(self, x):
        if isinstance(x, (int, float)):
            return self.__scale__(1 / x)

        if isinstance(x, Super):
            raise TypeError('Cannot divide types %s and %s. '
            'You need to extract a specific component, e.g., a.s / b.s' %
            (type(self).__name__, type(x).__name__))

        if not isinstance(x, Ys):
            raise TypeError("Unsupported types for /: 'Isuper' and '%s'" %
                            type(x).__name__)
        return self * Zs(1 / x)

    def __truediv__(self, x):
        return self.__div__(x)

    def cpt(self):
        from .oneport import I
        # Perhaps should generate more specific components such as Idc?        
        return I(self.time())

from .cexpr import Iconst, Vconst, cExpr        
from .fexpr import fExpr    
from .sexpr import Is, Vs, Ys, Zs, sExpr
from .texpr import It, Vt, tExpr
from .noiseexpr import In, Vn, noiseExpr
from .phasor import Iphasor, Vphasor, Phasor
from .omegaexpr import omegaExpr
from .symbols import s
