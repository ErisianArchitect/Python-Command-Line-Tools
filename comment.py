"""
This is a command line program to generate comments for
various programming languages.

Currently Supported Languages:
	None
"""

import sys

# Because this program will use arguments like a command
# stack, it will have to parse the arguments without 
# external libraries.

# Usage:
# 	Forms of input:
#	[Indented]
# 		0:"No Indentation"
#		"No Indentation"
# 		1:"One indentation unit."
# 		2:"Two indentation units."
#		3:"Three indentation units."
#	[io]
#		~"file.txt"
#		?"Prompt>"
#		@"Prompt"
#	'~' represents reading from a file.
#	'?' represents reading from the input stream.
#	'@' represents reading from an external editor, such as VS Code.
# comment.py [ "Header" 1:"Description" table(width=80)[ row[ left:"Left Justified" center:"Center Justified" right:"Right Justified" ] ] ]

# Because of the nature of how this program will work
# the arguments passed to the program will need to be
# processed in order to extract the information passed
# by the user.

##############################################################
#                        #                                   #

if __name__ == '__main__':
	for arg in sys.argv:
		print(arg)