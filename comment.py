"""
This is a command line program to generate comments for
various programming languages. This module requires no additional 
dependencies and can be run from the command line.

////////////////////////////////////////////////////////////////////////
//  Goals                                                             //
////////////////////////////////////////////////////////////////////////
-

////////////////////////////////////////////////////////////////////////
//  BELOW THIS LINE IS FOR TESTING PURPOSES                           //
////////////////////////////////////////////////////////////////////////

Here are some examples of styles that may be implemented. The line width
is set to 72 because that is what PEP guidelines dictate, and it is also
just a nice wrap width because it makes it easy to read lines when you 
have two files open side by side.

C Comment Style:

/***********************************************************************
 * This is how a comment box might look for C/C++ comments that wrap at
 * 72 characters. Notice that the maximum line width of any line is 72
 * characters and no more. This allows you to wrap information that is
 * viewable on the screen without scrolling horizontally. You can keep
 * no longer will need to scroll forever to read after line.
 ***********************************************************************
 * 		Each section is divided up and indented to your preference. User
 *     	indentation is also preserved. 
 *  		Indentation is implemented using tabs, which means that
 * 			similar indented lines will be on the same column number.
 *			If a user indented line is wrapped, the indentation will be
 * 			preserved for the wrapped line.
 **********************************************************************/

 C++ Box Comment Style:

////////////////////////////////////////////////////////////////////////
// This is an option for a C++ comment box. This comment box is also  //
// valid in other languages that use '//' as a comment prefix.        //
//--------------------------------------------------------------------//
// This comment box works the same as the above example. Indentation  //
// is preserved, lines are wrapped properly, etc.                     //
// One key difference with this comment style is that there is space  //
// at the end of the line followed by '//', which gives the whole     //
// comment a boxy style.                                              //
//--------------------------------------------------------------------//
// You can use many different divider styles.                         //
// Some of the divider styles are ugly, but you can still use them!   //
////////////////////////////////////////////////////////////////////////
// Divider Styles                                                     //
////////////////////////////////////////////////////////////////////////
//                                                                    //
//====================================================================//
//                                                                    //
//--------------------------------------------------------------------//
//                                                                    //
//********************************************************************//
//                                                                    //
//@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@//
//                                                                    //
//%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%//
//                                                                    //
//<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<//
//                                                                    //
//>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>//
//                                                                    //
//$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$//
//                                                                    //
//&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&&//
//                                                                    //
//!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!//
//                                                                    //
//:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::://
//                                                                    //
//;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;;//
//                                                                    //
//||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||||//
//                                                                    //
//++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++//
//                                                                    //
//....................................................................//
//                                                                    //
//,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,,//
//                                                                    //
//????????????????????????????????????????????????????????????????????//
//                                                                    //
//~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~//
//                                                                    //
//####################################################################//
//                                                                    //
//____________________________________________________________________//
//                                                                    //
//^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^//
//                                                                    //
////////////////////////////////////////////////////////////////////////
//                                                                    //
////////////////////////////////////////////////////////////////////////

C++ Open Comment Style:

////////////////////////////////////////////////////////////////////////
// The C++ Open Comment Style is similar to the above style, except that
// the text is able to extend all the way to the end of the width before
// wrapping to the next line. There are still dividers, the only change
// is that now the right side of the text area is open.
////////////////////////////////////////////////////////////////////////

Python Comment Style:

#-----------------------------------------------------------------------
# Text in your Python comment goes in here. Text is automatically
# wrapped, and indentation is preserved, as well as new lines and
# blank lines.
#
#-----------------------------------------------------------------------

Example command syntax:
python comment.py c "No indentation" [1]"Indentation level of 1. Zero is no indentation." [2]"Indentation level of 2."

+--
This is a header. The '+--' signifies the beginning of an area that should be parsed, and also marks the beginning of a header.
Everything will automatically be wrapped.


"""

import sys
import textwrap

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

# This function needed to be written in order to wrap the text while preserving
# empty lines.
def wrap_text(text : str, width : int = 72) -> list[str]:
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
            # This handy little trick lets us effectively insert lines into the list while overwriting the old line.
            lines[i:i+1] = textwrap.wrap(line, width)
    return lines

if __name__ == '__main__':
	for arg in sys.argv:
		print(arg)