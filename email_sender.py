
import smtplib
import json
from email.mime.text import MIMEText

CONFIG_FILE = "config_email.json"

def invia_email(oggetto, corpo):
    with open(CONFIG_FILE, "r") as f:
        config = json.load(f)

    mittente = config["email"]
    password = config["password"]
    destinatari = config["destinatari"]
    smtp_server = config["smtp_server"]
    smtp_port = config["smtp_port"]
    use_ssl = config.get("use_ssl", True)

    msg = MIMEText(corpo)
    msg["Subject"] = oggetto
    msg["From"] = mittente
    msg["To"] = ", ".join(destinatari)

    if use_ssl:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(mittente, password)
            server.sendmail(mittente, destinatari, msg.as_string())
    else:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(mittente, password)
            server.sendmail(mittente, destinatari, msg.as_string())
