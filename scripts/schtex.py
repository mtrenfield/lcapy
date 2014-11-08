#!/usr/bin/python
"""schtex V0.1
Copyright (c) 2014 Michael P. Hayes, UC ECE, NZ

Usage: schtex infile.sch [outfile.tex]
"""

from __future__ import print_function
from optparse import OptionParser
import sys
import os
from lcapy import Schematic


def main (argv=None):

    if argv is None:
        argv = sys.argv

    version = __doc__.split('\n')[0]

    parser = OptionParser(usage='%prog schematic-file', version=version, 
                          description=__doc__)

    parser.add_option('--label-nodes', action='store_true',
                      dest='label_nodes', default=True,
                      help='label nodes')

    parser.add_option('--s-model', action='store_true',
                      dest='s_model', default=False,
                      help='generate s-domain picture')
    
    (options, args) = parser.parse_args()

    if len(args) < 1:
        parser.error('missing argument')
        return 1

    filename = ''
    outfilename = ''
    if len(args) > 1:
        outfilename = args[1]
        filename = outfilename.replace('.pdf', '.pytex')

    infilename = args[0]
    if not infilename.endswith('.tex'):
        sch = Schematic(args[0])
        sch.draw(label_nodes=options.label_nodes, s_model=options.s_model,
                 filename=filename, tex=True)
    else:
        filename = infilename

    if not outfilename.endswith('.pdf'):
        return 0

    template = '\\documentclass[a4paper]{article}\n\\usepackage[americanvoltages]{circuitikz}\n\\begin{document}\n\\input %s\n\\end{document}' % filename

    tmpfile = open(outfilename.replace('.pdf', '.tex'), 'w')
    print(template, file=tmpfile)
    tmpfile.close()

    basename = os.path.splitext(outfilename)[0]
    print(basename)

    files = ' '.join([basename + ext for ext in ('.aux', '.log', '.pytex', '.tex')])
    
    # Should change directory if not simple path and use temporary filenames to avoid
    # collateral damage...
    os.system('pdflatex %s; rm ' % basename + files)

    return 0


if __name__ == '__main__':
    sys.exit(main())