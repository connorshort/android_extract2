//AT_CMD = 'AT\+|AT\*|AT!|AT@|AT#|AT\$|AT%|AT\^|AT&'
AT_CMD=('AT', 'AT\*', 'AT!', 'AT@', 'AT#', 'AT\$', 'AT%', 'AT\^', 'AT&')
def handle_text(filename):
	f=open(MY_TMP, 'a')
	with open(filename) as openfileobject:
    for line in openfileobject:
    	for word in AT_CMD:
    		if word in line:
    			#FIX OUTPUT TO MATCH AWK COMMAND ON LINE 321
    			f.write(line)

def handle_binary(filename):
	#WILL START OFF EXACT SAME AS TEXT

#NEXT TWO ARE JUST USING BINARY IN CURRENT EDITION
def handle_elf(filename):
	handle_binary(filename)
	# Can run bingrep, elfparser but they suck...

def handle_x86(filename):
	# Currently no special handling for x86 boot sectors
	handle_binary(filename)     