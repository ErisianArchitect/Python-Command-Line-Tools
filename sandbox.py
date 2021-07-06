"""
Preferred Python version: 3.9

This is a command line utility to start a Python interactive
interpreter that imports provided modules/scripts into the 
global namespace.
This is useful if you want to use a preconfigured interpreter.
In order for this to be achieved, a Python script must be
generated, then a new Python process is started with
    python -i <generated script path>
The generated script is then deleted upon exit.
"""

# python sandbox.py -i [os,subprocess,importlib.util]

# TODO: Currently, this script is broken. We'll have to review it later.

import os
import subprocess
import importlib.util
import tempfile
import click

def is_module_path(s : str) -> bool:
    """
    Checks if the provided string can be considered a valid module path.
    """
    if '.' in s:
        parts = s.split('.')
        for p in parts:
            if not p.isidentifier():
                return False
        return True
    else:
        return s.isidentifier()

def module_exists(name, path = None) -> bool:
    try:
        return importlib.util.find_spec(name, path) is not None
    except:
        return False

def check_module(name : str) -> bool:
    if not is_module_path(name):
        print(f'{repr(name)} is not a valid module name. Ignoring error and proceeding.')
        return False
    if not module_exists(name):
        print(f'Module {repr(name)} was not found. Ignoring error and proceeding.')
        return False
    return True

def split_module_parts(text : str):
    if '+' in text:
        left, right = text.split('+')
        member_names = right.split(',')
        return left, set(member_names)
    else:
        return text, set()

# Should the global injector inject double underscored variables?
# Should there be a filter (such as a regex filter) that can be optionally applied?
# Should there be an optional list of names to inject?

@click.command()
@click.option('-i', '--import', 'imports', type=str, required=False, multiple=True, help="Modules to import.")
@click.option('-m','--module','modules', type=str, required=False, multiple=True, help="Module globals are copied to interpreter globals.")
@click.option('-s', '--script', 'scripts', type=click.Path(exists=True, resolve_path=True), required=False, multiple=True, help="Script globals are copied to interpreter globals.")
def command_line(
    imports = (),
    modules = (),
    scripts = ()
    ):
    """
    Starts a Python interactive interpreter with chosen imports, as well as importing modules and scripts into globals.
    """
    if not modules and not scripts and not imports:
        print('No modules, scripts, or imports were provided. Aborting operation.')
    with tempfile.TemporaryDirectory() as d:
        script_path = os.path.join(d, 'interactive.py')
        with open(script_path, 'w') as f:
            # f.write(generated_source)

            # This function simply writes a line to the file.
            def putl(s : str, *extra):
                if type(s) is not str:
                    s = str(s)
                if extra:
                    s = ''.join([s, *extra])
                f.write(s)
                f.write('\n')
            putl('# Auto generated script for interactive shell.')
            # Add runpy to the auto generated script, give it a more unique name.
            # The unique name allows the user to import runpy if they wish without
            # interferance from the auto generated code.
            putl('import runpy as runpy_module_delete')
            # What we did with runpy above, we also do with importlib.
            putl('import importlib as importlib_module_delete')
            # We import sys in order to append the current working directory.
            # This is because this script is running from a temporary directory.
            # Since this script is running from a temporary directory, that means
            # that it will not know where the current working directory is.
            putl('import sys')
            putl('sys.path.append(', repr(os.getcwd()), ')')
            putl('del sys')

            # check_module() simply checks if the given name is a valid module name
            # and also checks if the module exists.

            # Steps:
            #   Check if there is @ symbol
            #   @ symbol represents a member you would like to import from module
            #   If not @ symbol exists, check for '=', which means <module>=<alias>
            #   Aliases also work for member names.
            #   So the possible syntax would be:
            #       -i math@sqrt,acos,sin,pow
            #       -i math@sqrt=math_sqrt,
            #       -i math=pymath
            
            for imp in imports:
                # Relative import
                if '@' in imp:
                    # imp would be a value like:
                    #   math@acos,sin,sqrt
                    # Where acos, sin, and sqrt are members that you want to import from math.
                    # We simply split with the '@' character, then the right side of that split
                    # is then split with the ',' character, getting our member names.
                    module_name, member_text = imp.split('@')
                    # We want to check if the module is a valid module before importing.
                    if not check_module(module_name):
                        continue
                    members = member_text.split(',')
                    def _filter(s : str):
                        """
                        Returns (identifier, alias)
                        If s does not contain '=', returns (identifier, identifier).
                        """
                        if '=' in s:
                            left, right = s.split('=')
                            return (left, right)
                        else:
                            return (s, s)
                    members = tuple(map(_filter, members))

                    putl('tmp = importlib_module_delete.import_module(', module_name, ').__dict__')
                    putl('tmp_members = [', ', '.join(map(repr, members)), ']')

                    putl('for mem in tmp_members:')
                    putl('\t', 'if mem[0] in tmp:')
                    putl('\t\t', 'globals()[mem[1]] = tmp[mem[0]]')

                    putl('del tmp_members')
                    putl('del tmp')

                # Alias import
                elif '=' in imp:
                    module_name, alias = imp.split('=')

                # Regular import
                else:
                    pass
                module_name = imp
                alias = None
                if '=' in imp:
                    module_name, alias = imp.split('=')
                if not check_module(module_name):
                    continue
                putl(alias, ' = importlib_module_delete.import_module(', repr(module_name), ')')
                if members:
                    putl('tmp_members = {', ', '.join(map(repr, members)), ' }')
                    putl('globals().update({ k : v for k, v in tmp.items() if k in tmp_members })')
                    putl('del tmp_members')
                else:
                    putl("globals().update({k : v for k, v in tmp.items() if not k.startswith('_') })")
            # This function is used to write generated code to                     
            def put_injection(func_name, arg, check = True):
                module_name, members = split_module_parts(arg)
                if check and not check_module(module_name):
                    return False
                # Get the globals from the module and store it in a temporary variable.
                putl('tmp = ', func_name, '(', repr(module_name), ')')
                putl('if type(tmp) is not dict:')
                putl('\t', 'tmp = tmp.__dict__')
                # Check if the user asked for specific members of the module (-m module:member1,member2,member3)
                if members:
                    putl('tmp_members = { ', ', '.join(map(lambda v: repr(v), members)), ' }')
                    putl('globals().update({ k : v for k, v in tmp.items() if k in tmp_members })')
                    putl('del tmp_members')
                else:
                    putl("globals().update({ k : v for k, v in tmp.items() if not k.startswith('_') })")
                putl('del tmp')
                return True
            for mod in modules:
                put_injection('importlib_module_delete.import_module', mod)
            for scr in scripts:
                put_injection('runpy_module_delete.run_path', scr, False)
            putl('del runpy_module_delete')
            putl('del importlib_module_delete')
        
        subprocess.call(['python', '-i', script_path])
        os.remove(script_path)

if __name__ == '__main__':
    command_line()