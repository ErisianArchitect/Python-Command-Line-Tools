"""
This is a command line utility for generating code.
It is a work in progress, and currently only supports
generating C-Style comments.
In the future, other languages will be supported as well.
"""

#requiered
import enum
import sys
import click
import re
import io
from io import StringIO
from pyperclip import copy
import random
import tempfile
import subprocess
import os
import shutil
import pathlib
import textwrap
from enum import Enum

char_range = lambda first, last: (chr(_) for _ in range(ord(first), ord(last) + 1))

__random_bits = [
    *char_range('0','9'),
    *char_range('A','Z')
]

def view_output(output, path=None):
    if path:
        abs_path = os.path.abspath(path)
        dir_name = pathlib.Path(os.path.dirname(abs_path))
        dir_name.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            print(repr(output))
            f.write(output)
    else:
        with tempfile.TemporaryDirectory() as d:
            out_path = os.path.join(d, 'output.cpp')
            with io.open(out_path, 'w', encoding='utf-8') as f:
                f.write(output)
            proc = subprocess.Popen([shutil.which('code'),'-n', out_path])
            while proc.poll() is None:
                if os.path.isfile(out_path):
                    proc.terminate()
                    break
        
            proc = subprocess.call([shutil.which('code'),'-n', out_path])

@click.group()
def command_line():
    pass

@command_line.command(name='cpp')
@click.option('/v', '--view', 'view',           required=False, is_flag=True, default=False)
@click.option('/r','--randomize' ,'randomize',  required=False, is_flag=True, default=True)
@click.option('/i', '--inside', 'inside',       required=False, is_flag=True, default=False)
@click.option('/c', '--copy', 'copyresult',     required=False, default=False, is_flag=True)
@click.option('/n', 'nocomments',               required=False, default=False, is_flag=True)
@click.option('-h', 'headers',                  required=False, multiple=True, default=None)
@click.option('-d', 'descriptions',             required=False, type=str, multiple=True, default=None)
@click.option('-r', 'regions',                  required = False, multiple=True, type=str)
@click.option('-b','--begin', 'begin_stmts',     multiple=True, is_flag=True)
@click.option('-e','--end', 'end_stmts',         multiple=True, is_flag=True)
@click.option('-c', 'setcomment',               multiple=True, is_flag=True)
@click.option('--guard', 'guard',               type=str, required = False)
@click.option('--out', 'output',                type=click.Path(exists=False, resolve_path=True),required=False, default=None)
@click.option('--width', 'width',               type=int, default=60, required = False)
@click.option('--indent', 'indent',             type=int, default=4, required = False)
@click.option('--prefix', 'prefix',             type=str, default = '[', required = False)
@click.option('--suffix', 'suffix',             type=str, default = ']', required = False)
def cmd_cpp(
            view = False,
       randomize = True,
          inside = False,
           guard = None,
           copyresult = False,
           nocomments = False,
         headers = (),
    descriptions = (),
      setcomment = (),
         regions = (),
         begin_stmts = (),
         end_stmts = (),
          output = None,
           width = 60,
          indent = 4,
          prefix = '[',
          suffix = ']',
    ):
    """
    gen.py -h"This is a header." -d"This is the description." -h"Another header." -d"Another description."
    """
    
    headers = list(headers)
    descriptions = list(descriptions)
    regions = list(regions)
    argv = sys.argv

    if '--copy' in os.environ:
        copyresult = True

    # The first step is to get the indices of all the region and description arguments.
    # The idea is that the description should come directly after the region.

    def output_result(s):
        if view:
            view_output(s, output)
        elif output is not None:
            abs_path = os.path.abspath(output)
            dir_name = pathlib.Path(os.path.dirname(abs_path))
            dir_name.mkdir(parents=True, exist_ok=True)
            with open(abs_path, 'w') as f:
                f.write(output)
            print(s)
            if copyresult:
                copy(s)
        else:
            print(s)
            if copyresult:
                copy(s)
    cmd_buffer = []
    hi = 0
    di = 0
    ri = 0

    lines = []

    for v in argv:
        if v[:2] == '-h':
            if headers[hi][0] == '?':
                headers[hi] = read_input(headers[hi][1:])
            elif headers[hi][0] == '~':
                headers[hi] = read_input(headers[hi][1:], external=True)
            elif headers[hi][0] == ':':
                headers[hi] = read_file(headers[hi][1:])
            cmd_buffer.append(header(headers[hi]))
            hi += 1
        elif v[:2] == '-d':
            if descriptions[di][0] == '?':
                descriptions[di] = read_input(descriptions[di][1:])
            elif descriptions[di][0] == '~':
                descriptions[di] = read_input(descriptions[di][1:])
            elif descriptions[di][0] == ':':
                descriptions[di] = read_file(descriptions[di][1:])
            cmd_buffer.append(description(descriptions[di]))
            di += 1
        elif v[:2] == '-c':
            lines.append(compound(cmd_buffer, width, indent))
            cmd_buffer.clear()
        elif v[:2] == '-r':
            if regions[ri][0] == '?':
                regions[ri] = read_input(regions[ri][1:])
            # elif regions[ri][0] == '~':
            #     regions[ri] = read_input(regions[ri][1:], external=True)
            # elif regions[ri][0] == ':':
            #     regions[ri] = read_file(regions[ri][1:])
            if not nocomments:
                cmd_buffer.insert(0, header(regions[ri]))
            note = compound(cmd_buffer, width, indent) if cmd_buffer else ''
            cmd_buffer.clear()
            if inside:
                lines.append(f'#pragma region {prefix}{regions[ri]}{suffix}')
                if not nocomments:
                    lines.append(note)
                lines.append(f'#pragma endregion {prefix}{regions[ri]}{suffix}')
            else:
                if not nocomments:
                    lines.append(note)
                lines.append(f'#pragma region {prefix}{regions[ri]}{suffix}')
                lines.append('\n\n')
                lines.append(f'#pragma endregion {prefix}{regions[ri]}{suffix}')
            ri += 1
    if cmd_buffer:
        lines.append(compound(cmd_buffer, width, indent))
        cmd_buffer.clear()
    
    if guard is not None:
        guard_title = comment(guard, None, width)
        m = re.compile(r'[\.\*\-\"\s]')
        guard_text = m.sub('_', guard).upper()
        if randomize:
            guard_text = guard_text + '__' + ''.join((random.choice(__random_bits) for _ in range(8)))
        lines.insert(0, '\n'.join([
            guard_title,
            f'#ifndef {guard_text} /* -{prefix}{guard}{suffix}- */\n#define {guard_text}',
            ''
        ]))
        lines.append('\n'.join([
            '#endif  /* -{prefix}{guard}{suffix}- */',
            comment('No code beyond this point...', None, width)
        ]))
    
    result = '\n'.join(lines)

    # result = f'#ifndef {guard_text} /* -{prefix}{guard}{suffix}- */\n#define {guard_text}\n\n{inner}\n\n/* No Code Beyond This Point... */\n#endif  /* -{prefix}{guard}{suffix}- */'
    output_result(result)

def read_file(path):
    if os.path.isfile(path):
        with io.open(path, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f'File was not found: {path}')
        return path

def read_input(prompt='Input', external=False):
    if not prompt:
        prompt = 'Input'
    if external:
        with tempfile.TemporaryDirectory() as d:
            ext_path = os.path.join(d, prompt)
            subprocess.call([shutil.which('code'),'-w', '-n', ext_path])
            if os.path.isfile(ext_path):
                with io.open(ext_path, 'r', encoding='utf-8') as f:
                    return f.read()
    else:
        return input(prompt + ': ')

class cmd_slot:
    __slots__ = ('value')
    def __init__(self, value):
        self.value = value

class header(cmd_slot): pass
class description(cmd_slot): pass

spacers = [' ' * i for i in range(200)]

lorem = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""

#python gen.py -h"Test Header" -d"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum." -h"Other" -d"Nothing"

def wrap_text(text : str, width):
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if line == '':
            lines[i] = ' '
        else:
            lines[i:i+1] = textwrap.wrap(line, width)
    return lines

def compound(args, width : int = 60, indent = 4):
    if not args:
        return ''
    for i, v in enumerate(args):
        pass
    if width > 200:
        width = 200
    if width < 12:
        width = 12
    if indent < 0:
        indent = 0
    if indent > 8:
        indent = 8
    edge_width = 6
    inner_width = width - edge_width
    indented_width = inner_width - indent
    _head = lambda t: ''.join(('//║ ', t, spacers[inner_width - len(t)], ' ║'))
    _body = lambda t: ''.join(('//║ ', spacers[indent] , t, spacers[indented_width - len(t)], ' ║'))

    def _header(v : str):
        wrapped = wrap_text(v, inner_width)
        return '\n'.join(map(_head, wrapped))
    
    def _description(v : str):
        wrapped = wrap_text(v, indented_width)
        return '\n'.join(map(_body, wrapped))

    top = ''.join(('//╔═', '═' * inner_width, '═╗'))
    divider = ''.join(('//╠═', '═' * inner_width, '═╣'))
    bottom = ''.join(('//╚═', '═' * inner_width, '═╝'))
    lines = [top]
    last_i = len(args) - 1
    for i, v in enumerate(args):
        v : cmd_slot
        end = i == last_i
        if type(v) == header:
            lines.append(_header(v.value))
        if type(v) == description:
            lines.append(_description(v.value))
        if not end:
            lines.append(divider)
    lines.append(bottom)

    return '\n'.join(lines)

def comment(title : str , info = None, width : int = 60, indent=0):
    if description is not None:
        return compound([header(title), description(info)], width, indent)
    else:
        return compound([header(title)], width, indent)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command_line()