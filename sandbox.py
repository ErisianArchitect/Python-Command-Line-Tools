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

# TODO: Currently, this script is broken. We'll have to review it later.

import os
import subprocess
import imp
import tempfile
import click

def is_module_name(s : str) -> bool:
    """
    Checks if the provided string can be considered a valid module name.
    """
    if '.' in s:
        parts = s.split('.')
        for p in parts:
            if not p.isidentifier():
                return False
        return True
    else:
        return s.isidentifier()

def module_path(name : str) -> str:
    """
    Gets the file location of the specified module.
    Returns None if the module was not found.
    """
    try:
        if not is_module_name(name):
            return None
        if '.' in name:
            name = name.split('.')[0]
        _, path, _ = imp.find_module(name)
        return path
    except ImportError:
        return None

def module_exists(name : str) -> bool:
    return bool(module_path(name))

def check_module(name : str) -> bool:
    if not is_module_name(name):
        print(f'{repr(name)} is not a valid module name. Ignoring error and proceeding.')
        return False
    if not module_exists(name):
        print(f'Module {repr(name)} was not found. Ignoring error and proceeding.')
        return False
    return True

def split_module_parts(text : str):
    if ':' in text:
        left, right = text.split(':')
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
def main(
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
            putl('import runpy as runpy_module_delete')

            for imp in imports:
                if not check_module(imp):
                    continue
                putl(f'import {imp}')
            def put_injection(func_name, arg):
                module_name, members = split_module_parts(arg)
                if not check_module(module_name):
                    return False
                # Get the globals from the module and store it in a temporary variable.
                putl('tmp = runpy_module_delete.', func_name, '(', repr(module_name), ')')
                # Check if the user asked for specific members of the module (-m module:member1,member2,member3)
                if members:
                    pass
                    putl('tmp_members = { ', ', '.join(map(lambda v: repr(v), members)), ' }')
                    putl("""globals().update({ k : v for k, v in tmp.items() if k in tmp_members })""")
                    putl('del tmp_members')
                else:
                    putl("""globals().update({ k : v for k, v in tmp.items() if not k.startswith('_') })""")
                putl('del tmp')
                return True
            for mod in modules:
                put_injection('run_module', mod)
            for scr in scripts:
                put_injection('run_path', scr)
            f.write('del runpy_module_delete')
        
        subprocess.call(['python', '-i', script_path])
        os.remove(script_path)

if __name__ == '__main__':
    main()