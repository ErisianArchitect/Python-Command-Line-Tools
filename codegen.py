#!/usr/bin/env python
"""
This is a command line utility for generating code.
It is a work in progress, and currently only supports
generating C-Style comments.
In the future, other languages will be supported as well.

I wrote this code specifically for my own usage, and it is designed
specifically for my system, but it should work similarly on a similar machine.

If you plan to use this script, there are certain parts that you may want to
modify to suit your needs.

In the future, I will work on documenting how this works and updating it to work better.

Currently, this code is janky, and probably doesn't work the way that it should.
That being said, it can do some nifty things.

Example usage:
    python codegen.py -h"This is a comment header" -d"This is a comment description. The description will have a different indentation than the header." -h"You can intersperse headers and descriptions" -c -d"The -c flag tells the program to write the previous statements to a single comment."
Output:
    // ╔════════════════════════════════════════════════════════╗
    // ║ This is a comment header                               ║
    // ╠════════════════════════════════════════════════════════╣
    // ║     This is a comment description. The description     ║
    // ║     will have a different indentation than the header. ║
    // ╠════════════════════════════════════════════════════════╣
    // ║ You can intersperse headers and descriptions           ║
    // ╚════════════════════════════════════════════════════════╝
    // ╔════════════════════════════════════════════════════════╗
    // ║     The -c flag tells the program to write the         ║
    // ║     previous statements to a single comment.           ║
    // ╚════════════════════════════════════════════════════════╝
    
The frame that you see around the text is made up of box-drawing characters, which are Unicode.
https://en.wikipedia.org/wiki/Box-drawing_character
If Unicode does not suit your needs, you should change the source code to remove those characters. (Look at the compound() function)
    
    
"""

#requiered
import enum
import sys
import click
import re
import io
from io import StringIO
import random
import tempfile
import subprocess
import os
import shutil
import pathlib
import textwrap
from enum import Enum
# For reading input and displaying output.
import tkinter as tk

char_range = lambda first, last: (chr(_) for _ in range(ord(first), ord(last) + 1))

_comment_prefixes = {
    'c'         : '// ',
    'py'    : '# ',
    'lua'       : '-- ',
}

__random_bits = [
    *char_range('0','9'),
    *char_range('A','Z')
]

def try_copy(text):
    try:

        # TODO: There is a way to use tkinter to copy to the clipboard.
        #       We should use tkinter as a fallback.
        import pyperclip
        pyperclip.copy(text)
    except ImportError:
        print("Unable to copy because pyperclip is not installed. (pip install pyperclip)")

def view_output(output, path=None):
    if path:
        abs_path = os.path.abspath(path)
        dir_name = pathlib.Path(os.path.dirname(abs_path))
        # TODO: Determine whether or not we really should make the parent directories.
        #       I feel like it may be a bad idea to do so.
        dir_name.mkdir(parents=True, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            print(repr(output))
            f.write(output)
    else:
        # This allows us to view the output in a window.
        # TODO: Now that we are using tkinter for viewing the output, we should also
        #       add an option to view the output with an external program.
        tkroot = tk.Tk()
        textview = tk.Text(tkroot, wrap='none')
        textview.insert(1.0, str(output))
        textview['state'] = 'disabled'
        textview.pack(expand=True, fill='both')
        
        tkroot.mainloop()

def has_var(name : str) -> bool:
    """
    Determines if `name` is in os.environ.
    This is a helper function for default values that can receive data from the environment variables.
    """
    return name in os.environ

@click.command()
@click.option('/v', '--view', 'view',           required=False, is_flag=True, default=has_var('--view'), help="View the output externally.")
@click.option('/r','--randomize' ,'randomize',  required=False, is_flag=True, default=has_var('--randomize'), help="Add random characters at the end of include guard to guarantee uniqueness.") # TODO: This option is for include guards. I should remove that.
@click.option('/i', '--inside', 'inside',       required=False, is_flag=True, default=has_var('--inside'), help="Write the comment inside of the region rather than outside.") # This option is only for if you are creating regions, which are only valid in select languages.
@click.option('/c', '--copy', 'copyresult',     required=False, is_flag=True, default=has_var('--copy'), help="Copy the output to the clipboard.")
@click.option('/n', 'nocomments',               required=False, is_flag=True, default=has_var('--nocomments'), help="Do not create comments.")
@click.option('-h', 'headers',                  required=False, multiple=True, default=None, help="A string that represents a comment header. (Like a title)")
@click.option('-d', 'descriptions',             required=False, multiple=True, default=None, help="A description that is indented.")
@click.option('-r', 'regions',                  required=False, multiple=True, default=None, help="Creates a region (C# or C/C++)")
@click.option('-b','--begin', 'begin_stmts',    multiple=True, is_flag=True, help="(Reserved for future use)")
@click.option('-e','--end', 'end_stmts',        multiple=True, is_flag=True, help="(Reserved for future use)")
@click.option('-c', 'setcomment',               multiple=True, is_flag=True, help="A flag to make a comment from the previous arguments.")
@click.option('--guard', 'guard',               type=str, required = False, help="Header guard string. (Likely to be removed in the future)")
@click.option('--out', 'output',                type=click.Path(exists=False, resolve_path=True), required=False, default=None, help="The path to write the output to.")
@click.option('--width', 'width',               type=int, required = False, default=60, help="The width of the comments. (This controls text wrapping)")
@click.option('--indent', 'indent',             type=int, required = False, default=4, help="The number of spaces to use for indentation.")
@click.option('--prefix', 'prefix',             type=str, required = False, default = '[', help="The prefix for the region name. (Will likely be removed in the future.)")
@click.option('--suffix', 'suffix',             type=str, required = False, default = ']', help="THe suffix for the region. (Will likely be removed in the future.)")
@click.option('--lang', 'lang',                 type=click.Choice(['c', 'py', 'lua']), required=False, default='c', help="The language to generate code for.")
def command_line(
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
          lang = 'c'
    ):
    # TODO: Update this docstring to better describe what this program does.
    """
    This program is used for generating some source code.
    Mostly it's for generating C-style comments. It does not currently support
    any other programming language comments.
    """
    
    headers = list(headers)
    descriptions = list(descriptions)
    regions = list(regions)
    argv = sys.argv

    def output_result(s):
        """
        This function is to output the result in some way.
        """
        # The --view flag was set, so we want to view the output in a window.
        # If `output` is not None, it will write to a file instead of showing
        # a window.
        if view:
            view_output(s, output)
        # If `output` is not None, we will write to a file.
        elif output is not None:
            abs_path = os.path.abspath(output)
            dir_name = pathlib.Path(os.path.dirname(abs_path))
            dir_name.mkdir(parents=True, exist_ok=True)
            with open(abs_path, 'w') as f:
                f.write(output)
            print(s)
        else:
            print(s)
        # If we want to copy the result, we will try to copy the result.
        if copyresult:
            try_copy(s)

    # Command Buffer which will be sent to the compound() function to create our generated code.
    cmd_buffer = []
    # Header index
    hi = 0
    # Description index
    di = 0
    # Region index
    ri = 0

    lines = []
    # The first step is to get the indices of all the region and description arguments.
    # The idea is that the description should come directly after the region.
    # This will loop through the arguments collecting the command arguments (-h, -d, -r, -c)
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
            lines.append(compound(cmd_buffer, width, indent, _comment_prefixes[lang]))
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
            note = compound(cmd_buffer, width, indent, _comment_prefixes[lang]) if cmd_buffer else ''
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
        lines.append(compound(cmd_buffer, width, indent, _comment_prefixes[lang]))
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

# TODO: Modify this so that it can use tkinter instead.
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

def compound(args, width : int = 60, indent = 4, prefix = _comment_prefixes['c']):
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
    _head = lambda t: ''.join((prefix, '║ ', t, spacers[inner_width - len(t)], ' ║'))
    _body = lambda t: ''.join((prefix, '║ ', spacers[indent] , t, spacers[indented_width - len(t)], ' ║'))

    def _header(v : str):
        wrapped = wrap_text(v, inner_width)
        return '\n'.join(map(_head, wrapped))
    
    def _description(v : str):
        wrapped = wrap_text(v, indented_width)
        return '\n'.join(map(_body, wrapped))

    top = ''.join((prefix, '╔═', '═' * inner_width, '═╗'))
    divider = ''.join((prefix, '╠═', '═' * inner_width, '═╣'))
    bottom = ''.join((prefix, '╚═', '═' * inner_width, '═╝'))
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