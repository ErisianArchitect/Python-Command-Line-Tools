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
I threw this code together in a rush to get it working, so now I'm working on rewriting it 
and figuring out what it actually needs to be.

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

// ╔════════════════════════════════════════════════════════╗
// ║ Future Plans                                           ║
// ╚════════════════════════════════════════════════════════╝

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
from functools import partial
from enum import Enum
# For reading input and displaying output.
import tkinter as tk

char_range = lambda first, last: (chr(_) for _ in range(ord(first), ord(last) + 1))

_comment_prefixes = {
    'cpp'         : '// ',
    'py'        : '# ',
    'lua'       : '-- ',
}

__random_bits = [
    *char_range('0','9'),
    *char_range('A','Z')
]

def clip_copy(text):
    """Copies text to the clipboard."""
    try:
        import pyperclip
        pyperclip.copy(text)
    except ImportError:
        # tkinter fallback if pyperclip is not installed.
        # https://stackoverflow.com/questions/11063458/python-script-to-copy-text-to-clipboard
        r = tk.Tk()
        r.withdraw()
        r.clipboard_clear()
        r.clipboard_append(str(text))
        r.update() # to keep it in the clipbard after the window is closed.
        r.destroy()

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
# TODO: Figure out this mess because this just is not right.
#       -o option should be used for output file
#       We're converting this to a comment generator, since it already is one.
@click.command()
@click.option('-h', 'headers',                  required=False, multiple=True, default=None, help="A string that represents a comment header. (Like a title)")
@click.option('-d', 'descriptions',             required=False, multiple=True, default=None, help="A description that is indented.")
@click.option('-r', 'regions',                  required=False, multiple=True, default=None, help="Creates a region (C# or C/C++)")
@click.option('-b','--begin', 'begin_stmts',    required=False, multiple=True, is_flag=True, help="(Reserved for future use)")
@click.option('-e','--end', 'end_stmts',        required=False, multiple=True, is_flag=True, help="(Reserved for future use)")
@click.option('-c', 'setcomment',               required=False, multiple=True, is_flag=True, help="A flag to make a comment from the previous arguments.")
@click.option('/v', '--view', 'view',           required=False, is_flag=True, default=has_var('--view'), help="View the output externally.")
@click.option('/r','--randomize' ,'randomize',  required=False, is_flag=True, default=has_var('--randomize'), help="Add random characters at the end of include guard to guarantee uniqueness.") # TODO: This option is for include guards. I should remove that.
@click.option('/i', '--inside', 'inside',       required=False, is_flag=True, default=has_var('--inside'), help="Write the comment inside of the region rather than outside.") # This option is only for if you are creating regions, which are only valid in select languages.
@click.option('/c', '--copy', 'copyresult',     required=False, is_flag=True, default=has_var('--copy'), help="Copy the output to the clipboard.")
@click.option('/n', 'nocomments',               required=False, is_flag=True, default=has_var('--nocomments'), help="Do not create comments.")
@click.option('--guard', 'guard',               required=False, type=str, help="Header guard string. (Likely to be removed in the future)")
@click.option('--out', 'output',                required=False, type=click.Path(exists=False, resolve_path=True), default=None, help="The path to write the output to.")
@click.option('--width', 'width',               required=False, type=int, default=72, help="The width of the comments. (This controls text wrapping)")
@click.option('--indent', 'indent',             required=False, type=int, default=4, help="The number of spaces to use for indentation.")
@click.option('--prefix', 'prefix',             required=False, type=str, default = '[', help="The prefix for the region name. (Will likely be removed in the future.)")
@click.option('--suffix', 'suffix',             required=False, type=str, default = ']', help="THe suffix for the region. (Will likely be removed in the future.)")
@click.option('--lang', 'lang',                 required=False, type=click.Choice(['cpp', 'py', 'lua']), default='cpp', help="The language to generate code for.")
def command_line(
         headers = (),
    descriptions = (),
         regions = (),
         begin_stmts = (),
         end_stmts = (),
      setcomment = (),
            view = False,
       randomize = True,
          inside = False,
           copyresult = False,
           nocomments = False,
           guard = None,
          output = None,
           width = 60,
          indent = 4,
          prefix = '[',
          suffix = ']',
          lang = 'cpp'
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
            clip_copy(s)

    # Command Buffer which will be sent to the compound() function to create our generated code.
    cmd_buffer = []
    # Header index
    hi = 0
    # Description index
    di = 0
    # Region index
    ri = 0

    lines = []
    # Let's rewrite the loop below.
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
            lines.append(compound_box(cmd_buffer, width, indent, _comment_prefixes[lang]))
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
            note = compound_box(cmd_buffer, width, indent, _comment_prefixes[lang]) if cmd_buffer else ''
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
        lines.append(compound_box(cmd_buffer, width, indent, _comment_prefixes[lang]))
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
        return input(prompt + ':')

class cmd_slot:
    __slots__ = ('value')
    def __init__(self, value):
        self.value = value

class header(cmd_slot): pass
class description(cmd_slot): pass

spacers = [' ' * i for i in range(200)]

lorem = """Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."""

#python codegen.py -h"Test Header" -d"Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum." -h"Other" -d"Nothing"

#======================================================================#
# wrap_text function                                                   #
#======================================================================#
_leading_whitespace_re = re.compile(r'^\s+')
# This function needed to be written in order to wrap the text while preserving
# empty lines.
# TODO: Adding tabs into the middle of a line can break wrapping algorithm somehow.
def wrap_text(text : str, width : int = 72, indent : int = 4) -> list[str]:
    """
    Wraps text to width and while preserving empty lines and
    indentation.

    returns lines as list of strings.
    """
    lines = text.splitlines()
    for i, line in enumerate(lines):
        # If the line is empty, just set the line to a space, otherwise wrap
        # the text.
        if line == '':
            lines[i] = ' '
        else:
            # Continue if the line doesn't need to be wrapped.
            if len(line) <= width:
                continue
            # Next, we read all whitespace at the beginning of the line.
            # This allows us to get the values for initial_indent and subsequent_indent.
            m = _leading_whitespace_re.match(line)
            line_indent = ''
            if m is not None:
                # Set line_indent to our matched whitespace.
                line_indent = line[:m.end()]
                # Remove the whitespace from the line.
                line = line[m.end():]
            # TODO: Solve how to wrap indented lines while keeping them at their indentation position.
            #       We might be able to achieve this by replacing all tabs with a number of spaces, or
            #       otherwise choosing a width for tabs to be.
            # This handy little trick lets us effectively insert lines into the list while overwriting the old line.
            lines[i:i+1] = textwrap.wrap(line, width, tabsize=indent, expand_tabs = True, initial_indent=line_indent, subsequent_indent=line_indent)
    return lines
_wrap_default_mapper = lambda v: v

def wrap_helper(towrap : str, width : int = 72, indent : int = 4, mapfunc = _wrap_default_mapper):
    """
    Helper function to wrap text then map the returned lines to a function and return the resulting string.
    Returns: argument towrap wrapped to the width provided and mapped using mapfunc
    """
    wrapped = wrap_text(towrap, width)
    return '\n'.join(map(mapfunc, wrapped))

def compound_box(args : list[cmd_slot], width : int = 72, indent : int = 4, prefix : str = _comment_prefixes['cpp'], margin = 1, **kwargs):
    """
    This creates a fancy box with word wrapped text. You shouldn't be calling this function unless you know what you're doing.
    """
    if not args:
        return ''
    # If you're trying to go above 200, no.
    if width > 200:
        width = 200
    if width < 12:
        width = 12
    if indent < 0:
        indent = 0
    if indent > 8:
        indent = 8
    box_left =          kwargs.get('box_left', '║ ')
    box_right =         kwargs.get('box_right', ' ║')
    box_topleft =       kwargs.get('box_topleft', '╔═')
    box_topright =      kwargs.get('box_topright', '═╗')
    box_divleft =       kwargs.get('box_divleft', '╠═')
    box_divright =      kwargs.get('box_divright', '═╣')
    box_bottomleft =    kwargs.get('box_bottomleft', '╚═')
    box_bottomright =   kwargs.get('box_bottomright', '═╝')
    box_div =           kwargs.get('box_div', '═')
    if type(margin) is int:
        margin_left = margin
        margin_right = margin
    elif type(margin) is tuple and len(margin) == 2:
        margin_left = margin[0]
        margin_right = margin[1]
    else:
        margin_left = 1
        margin_right = 1
    # edge_width is the width on the left and right side that is not
    # occupied by wrapped text. This includes the prefix, the left-box,
    # the left and right margins. This helps us to get the wrap width.
    edge_width = len(box_left) + len(box_right) + len(prefix) + (margin_left + margin_right)
    inner_width = width - edge_width
    indented_width = inner_width - indent
    _head = lambda t: ''.join((prefix, '║ ', t, spacers[inner_width - len(t)], ' ║'))
    _body = lambda t: ''.join((prefix, '║ ', spacers[indent] , t, spacers[indented_width - len(t)], ' ║'))


    _header = partial(wrap_helper, width=inner_width, indent=indent, mapfunc=_head)
    _description = partial(wrap_helper, width=indented_width, indent=indent, mapfunc=_body)

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
    if info is not None:
        return compound_box([header(title), description(info)], width, indent)
    else:
        return compound_box([header(title)], width, indent)

if __name__ == '__main__':
    if len(sys.argv) > 1:
        command_line()