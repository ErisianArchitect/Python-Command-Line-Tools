"""
This script is meant to be modified by the user to fit their needs.

The purpose of this script is for the following scenario:
	You have set up a certain directory in your file system to be active in the PATH.
	This allows you to call executables from that directory from the command line very easily.
You must configure this tool to have your own install directory.
"""

import os
import click

# You can set an environment variable called PYLOCALINSTALLPATH to your desired
# installation location.
install_directory = os.environ.get('PYLOCALINSTALLPATH') or '.'

# I think you can also run python as an archive. I'm gonna test it.

@click.command()
@click.argument('function', type=click.Choice(['install','uninstall']), required=True)
@click.argument('script', type=click.Path(file_okay=True, dir_okay=True, exists=False), required=True)
def command_line(function, script):

	if function == 'uninstall':
		install_path = os.path.join(install_directory, script + '.bat')
		if os.path.isfile(install_path):
			os.remove(install_path)
			print('Uninstalled!')
		else:
			print('Not found.')
		return
	if function != 'install':
		print(f'What the f*** did you put in? Oh, function:{repr(function)}')
		return
	script_path = os.path.abspath(script)
	script_name = os.path.splitext(os.path.basename(script_path))[0]

	batch_path = os.path.join(install_directory, script_name + '.bat')

	with open(batch_path, 'w') as bat:
		bat.write(f'@echo off\npython "{script_path}" %*')
	print(f'Created batch script at "{batch_path}"')
	print(f'Which points to "{script_path}"')

if __name__ == '__main__':
	command_line()