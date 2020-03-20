import requests
import sys

def blocked(url):
	try:
		r = requests.get(url)
		if r.status_code == 200:
			return False
		return True
	except:
		return True

if __name__ == "__main__":
	print(blocked(sys.argv[1]))
