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
@click.option('-i', '--import', 'imports', type=str, required=False, multiple=True, help = 'Module to import. Syntax: "-i module" or "-i module@member1,member2,member3" or "-i module=alias"')
@click.option('-s', '--script', 'scripts', type=click.Path(exists=True, resolve_path=True), required=False, multiple=True, help='Script file to execute and import globals from. Syntax: "-s script.py" or "-s script.py@member1,member2,member3"')
def command_line(
    imports = (),
    scripts = ()
    ):
    """
    Starts a Python interactive interpreter with chosen imports, as well as importing modules and scripts into globals.
    """
    if not scripts and not imports:
        print('No imports or scripts were provided. Aborting operation.')
    with tempfile.TemporaryDirectory() as d:
        script_path = os.path.join(d, 'interactive.py')
        with open(script_path, 'w') as f:
            # This function simply writes a line to the file.
            def putl(s : str, *extra):
                "Write line to open file."
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

            # Steps:
            #   Check if there is @ symbol
            #   @ symbol represents a member you would like to import from module
            #   If not @ symbol exists, check for '=', which means <module>=<alias>
            #   Aliases also work for member names.
            #   So the possible syntax would be:
            #       -i math@sqrt,acos,sin,pow
            #       -i math@sqrt=math_sqrt,
            #       -i math=pymath
            
            # We create a filter function for the members so that we can get aliases.
            # Aliases are represented in text with something like "module.path=alias"
            def alias_filter(s : str):
                """
                Returns (identifier, alias)
                If s does not contain '=', returns (identifier, identifier).
                """
                # If the '=' character is found, that means there is an alias.
                # We can find that alias by splitting with the '=' character.
                if '=' in s:
                    left, right = s.split('=')
                    # We return the left and right side of that split as a tuple.
                    return (left, right)
                else:
                    # If there is no alias, we will just return the input text
                    # as a tuple where both values are the input text.
                    return (s, s)
            
            # We loop through the imports provided by the user.
            for imp in imports:
                # Relative import
                if '@' in imp:
                    # imp would be a value like:
                    #   math@acos,sin,sqrt
                    # Where acos, sin, and sqrt are members that you want to import from math.
                    # We simply split with the '@' character, then the right side of that split
                    # is then split with the ',' character, getting our member names.
                    # The left side of the split is our module name.
                    module_name, member_text = imp.split('@')
                    # We want to check if the module is a valid module before importing.
                    if not check_module(module_name):
                        continue
                    # This is where we split the members.
                    # We create a new tuple of members filtered with the alias_filter function.
                    members = tuple(map(alias_filter, member_text.split(',')))
                    # Check if members is empty:
                    if not members:
                        print(f'No members provided for module <{module_name}>.')
                        continue
                    if len(members) == 1 and members[0] == '*':
                        # Write some generated code to import the module's dictionary into a temporary variable
                        putl('tmp = importlib_module_delete.import_module(', repr(module_name), ').__dict__')
                        putl('globals().update({ k : v for k, v in tmp.items() if not k.startswith("_") })')
                        putl('del tmp')
                    else:
                        cont_flag = False
                        for mem in members:
                            if not mem[1].isidentifier():
                                cont_flag = True
                                print(f'{repr(mem[1])} is not an identifier.')
                                break
                        if cont_flag:
                            continue
                        # Write some generated code to import the module's dictionary into a temporary variable
                        putl('tmp = importlib_module_delete.import_module(', repr(module_name), ').__dict__')
                        # Create a list of the temporary members in the generated code file
                        putl('tmp_members = [', ', '.join(map(repr, members)), ']')

                        # Loop through the temporary members, adding each to the globals with the alias name.
                        putl('for mem in tmp_members:')
                        putl('\t', 'if mem[0] in tmp:')
                        putl('\t\t', 'globals()[mem[1]] = tmp[mem[0]]')

                        # Now we must delete the temporary variables so they don't clutter
                        # up our global namespace.
                        putl('del tmp_members')
                        putl('del tmp')
                # Alias import
                elif '=' in imp:
                    # Get the module name and the alias we want to apply to that module.
                    module_name, alias = alias_filter(imp)
                    if not alias.isidentifier():
                        print(f'{repr(alias)} is not an identifier.')
                        continue
                    # Write our import line to the generated code file
                    putl(alias, ' = importlib_module_delete.import_module(', repr(module_name), ')')
                # Regular import
                else:
                    putl('import ', imp)
            # For the scripts, we will simply import all members into our global
            # namespace unless the user provides members that they would like to
            # specifically include using the '@' character.
            # Input might look like this:
            #   -s"script.py@function_1,function_2,function_3"
            # or
            #   -s script.py@function_1,function_2,function_3
            # or
            #   --script="script.py@function_1,function_2,function_3"
            for scr in scripts:
                # Check if we are importing specific members from the script.
                if '@' in scr:
                    # Separate the script name (module_name) from the members list.
                    module_name, member_text = scr.split('@')
                    # Check that the file exists, continue if it doesn't (Click should have already done so)
                    if not os.path.isfile(module_name):
                        print('Script does not seem to exist.\n', 'Path:', repr(module_name))
                        continue
                    # Create a tuple of members filtered through the alias_filter.
                    members = tuple(map(alias_filter, member_text.split(',')))
                    # Check if members is empty, continuing if it is.
                    if not members:
                        print(f'No members provided for script {repr(module_name)}')
                        continue
                    # Create a temporary variable to store the globals of the script that will be run.
                    putl('tmp = runpy_module_delete.run_path(', repr(module_name), ')')
                    # Create a list of the members that we want to add within the generated script.
                    putl('tmp_members = [', ', '.join(map(repr, members)), ']')
                    # loop through the members, attempting to add them to the globals dictionary.
                    putl('for mem in tmp_members:')
                    putl('\t', 'if mem[0] in tmp:')
                    putl('\t\t', 'globals()[mem[1]] = tmp[mem[0]]')
                    # We can also optionally print a message to the user telling them if a member was
                    # not found, and as such, not imported into the globals dictionary.

                    # Delete our temporary variables.
                    putl('del tmp_members')
                    putl('del tmp')
                # There is no '@' character in the provided input
                # This means that it is a raw path, and we should treat it as such.
                else:
                    # Our path does not exist, so we tell the user and continue.
                    if not os.path.isfile(scr):
                        print('Script does not seem to exist.\n', 'Path:', repr(scr))
                        continue
                    # Run the script at path, store the dictionary as a temporary variable `tmp`
                    putl('tmp = runpy_module_delete.run_path(', repr(scr), ')')
                    # Update the globals with values from tmp that do not start with '_'
                    putl('globals().update({ k : v for k, v in tmp.items() if not k.startswith("_") })')
                    # Delete our temporary variable to cleanup the global namespace.
                    putl('del tmp')
            # Delete our temporary modules to cleanup the global namespace.
            putl('del runpy_module_delete')
            putl('del importlib_module_delete')
        
        # Now we call Python with the -i (interactive) flag and pass in our generated script path
        # By calling Python with the -i flag set, this allows us to execute our generated script
        # then continue as the Python interactive interpreter after executing, thereby populating
        # the global namespace with the globals from the generated script.
        subprocess.call(['python', '-i', script_path])
        # We no longer need the script, so we delete it with os.remove
        # (The file should automatically be removed after leaving scope because we are in a temporary directory)
        os.remove(script_path)

# We didn't import this script as a module, so run the command_line function.
if __name__ == '__main__':
    command_line()