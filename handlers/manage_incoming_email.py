#!/usr/bin/env python
# (c) Baltasar 2018 MIT License <baltasarq@gmail.com>


import logging
import webapp2
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
import datetime as dt


class IncomingEmailHandler(InboundMailHandler):
    def receive(self, mail_msg):
        today = dt.datetime.today()
        body = [body.body.decode() + "\n" for body in mail_msg.bodies("text/plain")]

        error_msg = unicode(today) + " ERROR:\n" + body
        logging.error(error_msg)


app = webapp2.WSGIApplication(
    [InboundMailHandler.mapping()],
    debug=True)
