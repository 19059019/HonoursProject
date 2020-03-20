import getpass
import requests
from lxml import html

TEST_LOGIN = "http://0.0.0.0:5000/testloggedin"
SSO = "http://0.0.0.0:5000/cas/login"

def login(su_id, session):
    '''
    This function attempts to log into the webapp
    and returns whether it was successfull or not
    '''
    login = session.get(SSO)
    login_html = html.fromstring(login.text)
    hidden_elements = login_html.xpath('//form//input[@type="hidden"]')
    form = {x.attrib['name']: x.attrib['value'] for x in hidden_elements}
    form['username'] = su_id
    form['password'] = getpass.getpass()
    session.post(login.url, data=form)
    return session.get(TEST_LOGIN).text == "true"

if __name__ == "__main__":
    session = requests.Session()
