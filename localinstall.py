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
@click.argument('script', type=click.Path(file_okay=True, exists=True), required=True)
def command_line(script):
	script_path = os.path.abspath(script)
	script_basename = os.path.basename(script_path)
	script_name = os.path.splitext(script_basename)[0]

	batch_path = os.path.join(install_directory, script_name + '.bat')

	batch_script = f'python "{script_path}" %*'

	with open(batch_path, 'w') as bat:
		bat.write(batch_script)
	print('Created batch script pointing to provided script.')

if __name__ == '__main__':
	command_line()