import smtplib
import configparser
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import config

tokens = config.tokens
config = config.config
config= config["ams"]
survey_link = config["survey"]
gmail_user = config["email"]
gmail_password = config["password"]

def verify_token(request):
    """
    Ensure that the token valid
    """
    print(request.form.get("token"))
    if request.form.get("token") in tokens.values():
        return True
    return False
    
def send_email(request):
    """
    Send notification email to student
    """
    ass_code = request.form.get("ass_code")
    suid = request.form.get("suid")
    sent_from = gmail_user
    to = "{}@sun.ac.za".format(suid)
    subject = "Submission System Feedback - {}".format(ass_code)
    body = ""
    with open(config["template_path"], "r") as email:
        body = email.read()
    body = body.format(gmail_user, to, subject, survey_link)

    try:
        server = smtplib.SMTP(config["server"])
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to, body)
        server.quit()
        logging.debug("Email sent to {}".format(suid))
        return {"Status":"Success"}
    except Exception as e:
        logging.error(e)
        return {"Status":"Failure"}