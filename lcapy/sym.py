from .config import exclude, aliases
from sympy.parsing.sympy_parser import parse_expr, auto_number, rationalize
try:
    from sympy.parsing.sympy_parser import NUMBER, NAME, OP        
except:
    from sympy.parsing.sympy_tokenize import NUMBER, NAME, OP
    
from sympy import Basic, Symbol, Expr, Atom
from sympy.core.function import AppliedUndef
import sympy as sym
import re
from .context import context

__all__ = ('symsymbol', 'sympify', 'simplify')


global_dict = {}
exec('from sympy import *', global_dict)

for _symbol in exclude:
    global_dict.pop(_symbol)

for _alias, _name in aliases.items():
    global_dict[_alias] = global_dict[_name]


cpt_names = ('C', 'E', 'F', 'G', 'H', 'I', 'L', 'R', 'V', 'Y', 'Z')
cpt_name_pattern = re.compile(r"(%s)([\w']*)" % '|'.join(cpt_names))

sub_super_pattern = re.compile(r"([_\^]){([\w]+)}")


def capitalize_name(name):

    return name[0].upper() + name[1:]


def canonical_name(name):
    """Convert symbol name to canonical form for SymPy to recognise.

    R_{out} -> R_out
    R1 -> R_1
    """

    def foo(match):
        return match.group(1) + match.group(2)

    if not isinstance(name, str):
        return name

    # Convert R_{out} to R_out for SymPy to recognise.
    name = sub_super_pattern.sub(foo, name)

    if name.find('_') != -1:
        return name

    # Rewrite R1 as R_1, etc.
    match = cpt_name_pattern.match(name)
    if match:
        if match.groups()[1] == '':
            return name
        name = match.groups()[0] + '_' + match.groups()[1]
        return name

    return name


def symbols_find(arg):
    """Return list of symbols in arg.  No symbols are cached."""

    symbols = []

    def find_symbol(tokens, local_dict, global_dict):
        
        for tok in tokens:
            tokNum, tokVal = tok
            if tokNum == NAME:
                name = tokVal
                if name not in local_dict and name not in global_dict:
                    symbols.append(name)
        return ([(NUMBER, '0')])

    if isinstance(arg, str):
        parse_expr(arg, transformations=(find_symbol, ), 
                   global_dict=global_dict, local_dict={}, evaluate=False)
        
        return symbols

    # Hack
    if hasattr(arg, 'expr'):
        arg = arg.expr

    if not isinstance(arg, (Symbol, Expr, AppliedUndef)):
        return []
    return [repr(symbol) for symbol in arg.atoms(Symbol, AppliedUndef)]


def parse(string, symbols={}, evaluate=True, local_dict={}, **assumptions):
    """Handle arbitrary strings that may refer to multiple symbols."""

    cache = assumptions.pop('cache', True)

    def auto_symbol(tokens, local_dict, global_dict):
        """Inserts calls to ``Symbol`` or ``Function`` for undefined variables/functions."""
        result = []

        tokens.append((None, None))  # so zip traverses all tokens
        for tok, nextTok in zip(tokens, tokens[1:]):
            tokNum, tokVal = tok
            nextTokNum, nextTokVal = nextTok
            if tokNum == NAME:
                name = tokVal
                if name in global_dict:

                    obj = global_dict[name]
                    if isinstance(obj, (Basic, type)):
                        result.append((NAME, name))
                        continue

                    if callable(obj):
                        result.append((NAME, name))
                        continue

                name = canonical_name(str(name))

                if name in local_dict:
                    # print('Found %s' % name)
                    # Could check assumptions.
                    result.append((NAME, name))
                    continue

                # Automatically add Function.  We ignore the assumptions.
                # These could be supported by modifying fourier.py/laplace.py
                # to propagate assumptions when converting V(s) to v(t), etc.
                if nextTokVal == '(':
                    result.extend([(NAME, 'Function'),
                                   (OP, '('), (NAME, repr(name)), (OP, ')')])
                    continue

                # Automatically add Symbol                
                result.extend([(NAME, 'Symbol'),
                               (OP, '('), (NAME, repr(name))])
                for assumption, val in assumptions.items():
                    result.extend([(OP, ','), 
                                   (NAME, '%s=%s' % (assumption, val))])
                result.extend([(OP, ')')])

            else:
                result.append((tokNum, tokVal))

        return result

    s = parse_expr(string, transformations=(auto_symbol, auto_number,
                                            rationalize), 
                   global_dict=global_dict, local_dict=local_dict,
                   evaluate=evaluate)
    if not cache:
        return s

    # Look for newly defined symbols/functions.
    for symbol in s.atoms(Symbol, AppliedUndef):
        name = repr(symbol)
        if name not in symbols:
            symbols[name] = symbol

    return s


def sympify1(arg, symbols={}, evaluate=True, **assumptions):
    """Create a SymPy expression.

    The purpose of this function is to head SymPy off at the pass and
    apply the defined assumptions.

    """

    if hasattr(arg, 'expr'):
        return arg.expr

    if isinstance(arg, (Symbol, Expr)):
        return arg

    # Why doesn't SymPy do this?
    if isinstance(arg, complex):
        re = sym.sympify(str(arg.real), rational=True, evaluate=evaluate)
        im = sym.sympify(str(arg.imag), rational=True, evaluate=evaluate)
        if im == 1.0:
            arg = re + sym.I
        else:
            arg = re + sym.I * im
        return arg

    if isinstance(arg, float):
        # Note, need to convert to string to achieve a rational
        # representation.
        return sym.sympify(str(arg), rational=True, evaluate=evaluate)
        
    if isinstance(arg, str):
        # Handle arbitrary strings that may refer to multiple symbols.
        return parse(arg, symbols, evaluate=evaluate,
                     local_dict=symbols, **assumptions)

    return sym.sympify(arg, rational=True, locals=symbols, 
                       evaluate=evaluate)


def sympify(expr, evaluate=True, **assumptions):
    """Create a SymPy expression.

    By default, symbols are assumed to be positive unless real is
    defined.

    """
    
    if 'real' not in assumptions and 'positive' not in assumptions:
        assumptions['positive'] = True
    return sympify1(expr, context.symbols, evaluate, **assumptions)


def symsymbol(name, **assumptions):
    """Create a SymPy symbol.

    By default, symbols are assumed to be positive unless real is
    defined.

    """
    return sympify(name, **assumptions)


def symsimplify(expr):
    """Simplify a SymPy expression.  This is a hack to work around
    problems with SymPy's simplify API."""

    # Handle Matrix types
    if hasattr(expr, 'applyfunc'):
        return expr.applyfunc(lambda x: symsimplify(x))
    
    try:
        if expr.is_Function and expr.func in (sym.Heaviside, sym.DiracDelta):
            return expr
    except:
        pass

    expr = sym.simplify(expr)
    return expr


def simplify(expr):
    """Simplify an Lcapy expression."""

    try:
        return expr.simplify()
    except:
        pass
    
    try:
        expr = expr.expr
    except:
        pass
    return symsimplify(expr)


def is_sympy(expr):
    return isinstance(expr, (Symbol, Expr, AppliedUndef))


def symdebug(expr, s='', indent=0):

    def _debug_args(args, s='', indent=0):

        for m, arg in enumerate(args):
            s = symdebug(arg, s, indent)
            if m == len(expr.args) - 1:
                s += ')\n'
            else:
                s += ',\n' + ' ' * indent
        return s

    if isinstance(expr, Symbol):
        s += str(expr) + ': %s' % expr.assumptions0

    elif isinstance(expr, Atom):                
        s += str(expr)

    elif isinstance(expr, Expr):
        
        name = expr.__class__.__name__
        s += '%s(' % name
        s = _debug_args(expr.args, s, indent + len(name) + 1)

    elif isinstance(expr, AppliedUndef):
        name = expr.func.__name__
        s += name
        s = _debug_args(expr.args, s, indent + len(name) + 1)

    return s


ssym = symsymbol('s', real=False)
tsym = symsymbol('t', real=True)
fsym = symsymbol('f', real=True)
omegasym = symsymbol('omega', real=True)

pi = sym.pi
j = sym.I
oo = sym.oo
inf = sym.oo
