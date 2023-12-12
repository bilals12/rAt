import socket

# some common ports
ports = [21, 22, 23, 25, 53, 80, 110, 111, 135, 139, 143, 179, 443, 445,
         514, 993, 995, 1723, 3306, 3389, 5900, 8000, 8080, 8443, 8888]

def single_host(ip):
	"""[%] perform a simple port scan on a single host [%]"""
	try:
		# validate IP first
		socket.inet_aton(ip)
	except socket.error:
		return '[!] invalid IP address [!]'

	results = ''
	socket.setdefaulttimeout(0.5) # default timeout for all socket ops

	for port in ports:
		with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
			result = s.connect_ex((ip, port))
			state = 'open' if result == 0 else 'closed'
			results += '{:>5}/tcp {:>7}\n'.format(port, state)

	return results.rstrip()