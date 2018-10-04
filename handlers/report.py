#!/usr/bin/env python
# (c) Baltasar 2018 MIT License <baltasarq@gmail.com>


import webapp2
from google.appengine.api.mail import EmailMessage
import datetime as dt


from model.appinfo import AppInfo
from model.ticket import Ticket


class ReportHandler(webapp2.RequestHandler):
    def get(self):
        today = dt.datetime.today()

        if (today.weekday() < 5
        and today.month != 8):
            message_body = "Daily report\n\nPending open tickets\n\n===\n\n"
            tickets = Ticket.query(Ticket.status == Ticket.Status.Open).order(-Ticket.added)

            for ticket in tickets:
                message_body += unicode(ticket) + "\n\n---\n\n"

            message_body += "\n\n---\n\n" + AppInfo.AppWeb + "\n"

            EmailMessage(
                    sender=AppInfo.AppEmail,
                    subject=AppInfo.Name + " report: " + today.strftime("%Y-%m-%d %H:%M:%S"),
                    to=AppInfo.BroadcastEmail,
                    body=message_body).send()

            self.redirect("/info?url=/manage_tickets&msg=Report sent to: "
                          + AppInfo.BroadcastEmail.decode("ascii", "replace"))
        else:
            self.redirect("/info?url=/manage_tickets&msg=Report only to be sent 9h mon-fri, except on august")


app = webapp2.WSGIApplication([
    ("/report", ReportHandler),
], debug=True)
