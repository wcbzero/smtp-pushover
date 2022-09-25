#!/usr/bin/env python
# -*- coding: utf-8 -*-
import base64
import email
import http.client
import json
import os
import urllib
from loguru import logger
import aiosmtpd.smtp
from aiosmtpd.controller import Controller

smtp_bind_address = os.environ.get('SMTP_BIND_ADDRESS', '0.0.0.0')
smtp_bind_port = int(os.environ.get('SMTP_BIND_PORT', 25))
pushover_domain = os.environ.get('PUSHOVER_DOMAIN', 'api.pushover.net')
pushover_port = str(os.environ.get('PUSHOVER_PORT', '443'))
pushover_user = os.environ.get('PUSHOVER_USER')
pushover_api_token = os.environ.get('PUSHOVER_API_TOKEN')


def send_pushover_message(message):
    conn = http.client.HTTPSConnection(f"{pushover_domain}:{pushover_port}")
    conn.request("POST", "/1/messages.json",
                 urllib.parse.urlencode({
                     "token": pushover_api_token,
                     "user": pushover_user,
                     "message": message,
                 }), {"Content-type": "application/x-www-form-urlencoded"})
    conn.getresponse()


def get_email_body(emailobj):
    """ Return the body of the email, preferably in text.
    """

    def _get_body(emailobj):
        """ Return the first text/plain body found if the email is multipart
        or just the regular payload otherwise.
        """
        if emailobj.is_multipart():
            for payload in emailobj.get_payload():
                # If the message comes with a signature it can be that this
                # payload itself has multiple parts, so just return the
                # first one
                if payload.is_multipart():
                    return _get_body(payload)

                body = payload.get_payload()
                if payload.get_content_type() == "text/plain":
                    return body
        else:
            return emailobj.get_payload()

    body = _get_body(emailobj)

    enc = emailobj["Content-Transfer-Encoding"]
    if enc == "base64":
        body = base64.decodestring(body)

    return body


class SmtpPushoverHandler:
    async def handle_DATA(self, server, session, envelope: aiosmtpd.smtp.Envelope):
        # Get the text of the message
        message_text = envelope.content.decode('utf8', errors='replace')
        # Get a python email object
        message = email.message_from_string(message_text)
        # Extract the body of the message
        body = get_email_body(message)
        # Send just the body
        send_pushover_message(f'{message["subject"]}.\n{body}')
        logger.info(
            f'Sent message from "{envelope.mail_from}". Subject {message["subject"]} content: {json.dumps(body)}')
        return '250 Message accepted for delivery'


if __name__ == '__main__':
    handler = SmtpPushoverHandler()
    controller = Controller(handler, hostname=smtp_bind_address, port=smtp_bind_port)
    # Run the event loop in a separate thread.
    controller.start()
    # Wait for the user to press Return.
    input('SMTP server running. Press Return to stop server and exit.')
    controller.stop()
