import requests
import time
import lxml.html
from bs4 import BeautifulSoup

###############################################################################
# Gets the Beuatiful Soup of the content of a url, using the Requests and bs4
# packages.
#
# If the first request fails, there will be two more attwmpt before EMPTY is
# returned.
#
# in:
#   url - url of required webpage
#   debug - debug value
# out:
#   Either "EMPTY" or the soup of the given url
###############################################################################


def get_soup(url, debug=0):
    for i in range(3):
        with requests.session() as session:
            try:
                time.sleep(0.01)
                request = session.get(url)
                return BeautifulSoup(request.content, "lxml")
            except:
                if debug != 0:
                    print("\nAttempt: %d\n" % i)
                else:
                    pass
    return "EMPTY"


if __name__ == "__main__":
    domains = set()
    # List of google domains
    soup = get_soup(
        "https://ipfs.io/ipfs/QmXoypizjW3WknFiJnKLwHCnL72vedxjQkDDP1mXWo6uco/wiki/List_of_Google_domains.html"
    )
    for section in soup.find_all("span", {"class": "url"}):
        text = section.find("a").text
        domains.add("www.{}".format(text))
        domains.add("drive.{}".format(text))
        domains.add("docs.{}".format(text))
    with open("shellScripts/google_domains.txt", "w+") as file:
        file.write("# Block all google domains\n")
        for domain in domains:
            file.write("127.0.0.1 {}\n".format(domain))
        file.write("\n")

