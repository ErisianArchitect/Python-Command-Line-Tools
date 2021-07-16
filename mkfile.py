"""
This script creates one or more files at the specified locations.
I wrote this script because I use Windows 10, and it's
nice to have a way to create empty files from the command line.
"""

import os, sys
import click
import pathlib
import shutil
import subprocess

# First check for the DEFAULTEDITOR environtment variable.
# If that is not found, we check if VS Code is installed
# by looking for the 'code' command.
# If VS Code is not found, we find notepad, which should
# be on all Windows machines.
_default_editor = os.environ.get('DEFAULTEDITOR', None) or shutil.which('code') or shutil.which('notepad')

@click.command()
@click.option('--editor', 'editor', required=False, default=_default_editor, help="Default editor to open if [-o|--open] flag is set.")
@click.option('-o', '--open', 'open_in_editor', required = False, is_flag = True, default = False, help="Open in external editor. (VS Code)")
@click.argument('paths', required=True, nargs=-1)
def main(
    editor = _default_editor,
    open_in_editor = False,
    paths = ()
    ):
    """
    Creates file(s) (and resolves directories) at specified path(s).
    This attempts to mimic the `touch` command in Linux.
    """
    if len(paths) == 0:
        print('No paths provided. Aborting!')
        return
    for i, path in enumerate(paths):
        # Get the absolute path.
        abs_path = os.path.abspath(path)
        # Get the directory path.
        dir_path = pathlib.Path(os.path.dirname(abs_path))
        # Force the directories to be created.
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create empty file at absolute path.
        with open(abs_path, 'w'): pass
        # If we need to open in the external editor, we will open VS Code.
        # In the future, we can add another option for what command to run
        # to open the files.
        if open_in_editor:
            subprocess.call([editor, abs_path])
    # We want to tell the user that their file(s) have been created.
    # We check if there is only one file or multiple files that have been
    # created in order determine whether or not 'File' needs to be plural
    # in the output.
    if len(paths) > 1:
        print('Files created!')
    else:
        print('File created!')

if __name__ == '__main__':
    main()