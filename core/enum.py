import ctypes
import getpass
import os
import platform
import socket
import time
import urllib.request
import uuid

enum_format = '''
platform				- {}
processor				- {}
architecture			- {}
internal IP				- {}
external IP 			- {}
MAC						- {}
internal hostname		- {}
external hostname		- {}
hostname aliases		- {}
FQDN					- {}
current user			- {}
system datetime			- {}
admin access			- {}'''

def run(plat):
	"""[@@] run system enumeration + return results [@@]"""

	# OS info
	sys_platform = platform.platform()
	processor = platform.processor()
	architecture = platform.architecture()[0]

	# session info
	username = getpass.getuser()

	# network info
	hostname = socket.gethostname()
	fqdn = socket.getfqdn()
	try:
		internal_ip = socket.gethostbyname(hostname)
	except socket.gaierror:
		internal_ip = '[!] unavailable [!]'

	raw_mac = uuid.getnode()
	mac = ':'.join(('%012X' % raw_mac)[i:i+2] for i in range(0, 12, 2))

	# get external IP
	ex_ip_grab = ['ipinfo.io/ip', 'icanhazip.com', 'ident.me', 'ipecho.net/plain', 'myexternalip.com/raw', 'wtfismyip.com/text']
	external_ip = ''
	for url in ex_ip_grab:
		try:
			external_ip = urllib.request.urlopen(f'http://{url}').read().decode().rstrip()
		except IOError:
			pass
		if 6 < len(external_ip) < 16:
			break

	# reverse DNS lookup
	try:
		ext_hostname, aliases, _ = socket.gethostbyaddr(external_ip)
	except (socket.herror, NameError):
		ext_hostname, aliases = 'unavailable', []

	aliases = ', '.join(aliases) if aliases else 'none'

	# datetime
	dt = time.strftime('%a, %d %b %Y %H:%M:%S {}'.format(time,tzname[0]), time.localtime())

	# platform specific
	is_admin = False
	if plat == 'win':
		is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
	elif plat in ['nix', 'mac']:
		is_admin = os.getuid() == 0

	admin_access = 'yes' if is_admin else 'no'

	# return results
	return enum_format.format(sys_platform, processor, architecture, internal_ip, external_ip, mac, hostname, ext_hostname, aliases, fqdn, username, dt, admin_access)