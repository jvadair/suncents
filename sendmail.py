"""
Modified from sendmail.py from
https://github.com/jvadair/registrationAPI
which is licensed under the Apache 2.0 license
(c) James Adair 2023
"""
import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pyntree import Node
from flask import render_template
import os
from jinja2 import Template
from uuid import uuid4
from copy import copy
from db_connector import db, conn, engine, metadata

# Config
"""
This file looks for the following properties to be set in config.yml:
smtp.email:    str
smtp.password: str
smtp.server:   str
smtp.port:     int
"""

config = Node('config.yml')
settings = config.smtp


def associate_user(identifier, by_column="id"):
    users = db.Table("users", metadata, autoload_with=engine)
    q = db.select(users).where(
        users.c[by_column] == identifier
    )
    user = conn.execute(q).fetchone()
    return user


def send_template(template_path, subject, *recipients, ignore_unsubscribed=False, **kwargs):
    """
    Fill and send a Jinja template
    :param template_path: The HTML template to send
    :param subject: The subject of the email
    :param recipients: All emails receiving the message
    :param ignore_unsubscribed: You can choose to ignore users who have unsubscribed
    :param kwargs: Pass variables to the Jinja template
    :return:
    """
    recipients = list(recipients)
    if not ignore_unsubscribed:
        for recipient in recipients:
            user = associate_user(recipient)
            if user.noemails:
                recipients.remove(recipient)

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = settings.email()
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(settings.server(), settings.port(), context=context) as server:
        server.login(settings.email(), settings.password())
        for recipient in recipients:
            to_send = copy(message)
            to_send["To"] = recipient
            with open('templates/' + template_path, 'r') as file:
                html = Template(file.read()).render(**kwargs, web_url=config.web_url(), unsub_id=associate_user(recipient, by_column="email").id)
            to_send.attach(MIMEText(html, "html"))
            server.sendmail(
                settings.email(),
                recipient,
                to_send.as_string()
            )


def unsubscribe(user_id):
    if not user_id:
        return "No user id was provided.", 400
    user = associate_user(user_id)
    if not user:
        return "Invalid user id.", 400
    elif user.noemails:
        return "You have already unsubscribed.", 400
    else:
        users = db.Table("users", metadata, autoload_with=engine)
        q = db.update(users).where(
            users.c.id == user_id
        )
        conn.execute(q, {"noemails": True})
        conn.commit()
        return "You are no longer subscribed to emails from Suncents."
