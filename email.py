import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from time import strftime, localtime

# fromaddr = "Ali.attendence7422@gmail.com"
# toaddr = "H00292894@hct.ac.ae"

def send_email(fromaddr = "Ali.attendence7422@gmail.com", toaddr = "H00292894@hct.ac.ae"):
    t = localtime
    a = strftime("%d_%m_%y", t())
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Attendence for today"
    body = "Kindly refer to the following attachents."
    msg.attach(MIMEText(body, 'plain'))
    filename = "attendence_" + a + ".csv"
    attachment = open("attendence/"+"attendence_" + a + ".csv", "rb")
    p = MIMEBase('application', 'octet-stream')
    p.set_payload((attachment).read())
    encoders.encode_base64(p)
    p.add_header('Content-Disposition', "attachment; filename= %s" % filename)
    msg.attach(p)
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(fromaddr, "email@2028")
    text = msg.as_string()
    s.sendmail(fromaddr, toaddr, text)
    s.quit()