def calcFunc(func, values):
	newFunc = ""
	for ch in func:
		if ch in values:
			newFunc += str(values[ch])
		else:
			newFunc += ch
	try:
		return eval(newFunc)
	except:
		return False