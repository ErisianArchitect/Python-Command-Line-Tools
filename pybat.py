"""
This script allows the user to create .bat files that run their scripts.
You can configure it to place those .bat files in your own specified directory.
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

@click.group()
def command_line():
	pass

@command_line.command(name='install')
@click.argument('script', type=click.Path(file_okay=True,dir_okay=True, exists=True), required=True)
@click.argument('alias', type=str, required=False, default=None)
def install_command(script, alias = None):
	script_path = os.path.abspath(script)
	script_name = os.path.splitext(os.path.basename(script_path))[0]

	batch_path = os.path.join(install_directory, (alias if alias else script_name) + '.bat')

	with open(batch_path, 'w') as bat:
		bat.write(f'@echo off\npython "{script_path}" %*')
	print(f'Created batch script at "{batch_path}"')
	print(f'Which points to "{script_path}"')

@command_line.command(name='uninstall')
@click.argument('name', required=True)
def uninstall_command(name):
	install_path = os.path.join(install_directory, name + '.bat')
	if os.path.isfile(install_path):
		os.remove(install_path)
		print('Uninstalled!')
	else:
		print('Not found.')

if __name__ == '__main__':
	command_line()