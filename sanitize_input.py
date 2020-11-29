def sanitize(string):
	retStr = ""

	for ch in string:
		if(ch == '<'):
			retStr += '&lt;'
		if(ch == '>'):
			retStr += '&gt;'
		if(ch == '&'):
			retStr += '&amp;'
		if(ch == '"'):
			retStr += '&quot;'
		if(ch == '\''):
			retStr += '&apos;'
		else:
			retStr += str(ch)

	return retStr