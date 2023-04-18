"""
This script takes a Jupyter notebook, and:
1. Enumerates all headers (e.g. ## Header -> ## 1.1 Header)
2. Adds a table of contents at the top based on enumerated headers.

The TOC is added in a new markdown cell.
The items appearing in the TOC are all the markdown headers of the notebook.

Usage:
> add_enumeration_and_toc.py notebook.ipynb

Enumeration of headers developed by myself.

Code for table of contents taken from here: https://github.com/gerbaudo/python-scripts/blob/master/various/add_toc.py
... and slightly modified

"""

import os
import re
import sys

from collections import namedtuple

import nbformat
from nbformat.v4.nbbase import new_markdown_cell

TOC_COMMENT = "<!--TABLE OF CONTENTS-->\n"


Header = namedtuple('Header', ['level', 'name'])

def is_toc_comment(cell):
    return cell.source.startswith(TOC_COMMENT)
    

        
def enumerate_headers(nb):
    headers_nums = []
    RE = re.compile(r'(?:^|\n)(?P<level>#{1,6})(?P<header>(?:\\.|[^\\])*?)#*(?:\n|$)')
    
    def enumerate_the_header(m,headers_nums):
        level = m.group('level').strip().count('#')
        
        if level>0:
            while len(headers_nums)<level:
                headers_nums.append(0)
            headers_nums[level-1]=headers_nums[level-1]+1
            headers_nums[level:]=[0]*len(headers_nums[level:])
            return f"{m.group('level')} {'.'.join(str(x) for x in headers_nums[:level])}.{m.group('header')}\n"
        else:
            return m.string

    for cell in nb.cells:
        if is_toc_comment(cell):
            continue
        elif cell.cell_type=='markdown':
            if RE.match(cell.source):
               cell.source=RE.sub(lambda m: enumerate_the_header(m,headers_nums),cell.source)

def collect_headers(nb):
    headers = []
    RE = re.compile(r'(?:^|\n)(?P<level>#{1,6})(?P<header>(?:\\.|[^\\])*?)#*(?:\n|$)')
    
    for cell in nb.cells:
        if is_toc_comment(cell):
            continue
        elif cell.cell_type=='markdown':
            for m in RE.finditer(cell.source):
               
                header = m.group('header').strip()
                level = m.group('level').strip().count('#')
                headers.append(Header(level, header))
                print(level*'  ','-',header)
                
    return headers

def write_toc(nb_name,nb, headers):
    nb_file = os.path.basename(nb_name)

    def format(header):
        indent = (header.level-1)*(2*' ')
        name = header.name
        anchor = '#'+name.replace(' ','-')
        return f"{indent}- [{name}]({anchor})"
        
    def remove_unsupported_keys(cell_dict):
        #removing id key - otherwise GitHub nbviewer fails
        return cell_dict.pop('id',None)

    toc = TOC_COMMENT
    toc += '<b>Contents:</b>\n'
    toc += '\n'.join([format(h) for h in headers])

    first_cell = nb.cells[0]
    if is_toc_comment(first_cell):
        remove_unsupported_keys(first_cell)
        print("- amending toc for {0}".format(nb_file))
        first_cell.source = toc
    else:
        print("- inserting toc for {0}".format(nb_file))
        nb.cells.insert(0, new_markdown_cell(source=toc)) 
        first_cell = nb.cells[0]
        remove_unsupported_keys(first_cell)
    nbformat.write(nb, nb_name)
    
if __name__=='__main__':
    nb_name = sys.argv[1]
    nb = nbformat.read(nb_name, as_version=4)
    enumerate_headers(nb)
    headers = collect_headers(nb)
    write_toc(nb_name, nb, headers)
