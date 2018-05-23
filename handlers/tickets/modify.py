#!/usr/bin/env python
# coding: utf-8
# (c) Baltasar 2018 MIT License <baltasarq@gmail.com>


import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb
from webapp2_extras import jinja2

import model.user as usr_mgt
import model.ticket as tickets
from model.ticket import Ticket
from model.appinfo import AppInfo


class ModifyTicket(webapp2.RequestHandler):
    def get(self):
        try:
            id = self.request.GET['ticket_id']
        except KeyError:
            self.redirect("/error?msg=ticket was not found")
            return

        usr = users.get_current_user()
        usr_info = usr_mgt.retrieve(usr)

        if usr and usr_info:
            access_link = users.create_logout_url("/")

            try:
                ticket = ndb.Key(urlsafe=id).get()
            except:
                self.redirect("/error?msg=key #" + id + " does not exist")
                return

            template_values = {
                "info": AppInfo,
                "usr_info": usr_info,
                "access_link": access_link,
                "ticket": ticket,
                "Status": Ticket.Status,
                "Progress": Ticket.Progress,
                "Priority": Ticket.Priority,
                "Type": Ticket.Type,
            }

            jinja = jinja2.get_jinja2(app=self.app)
            self.response.write(jinja.render_template("modify_ticket.html", **template_values))
        else:
            self.redirect("/")

    def post(self):
        try:
            id = self.request.GET['ticket_id']
        except KeyError:
            id = None

        if not id:
            self.redirect("/error?msg=missing id for modification")
            return

        user = users.get_current_user()
        usr_info = usr_mgt.retrieve(user)

        if user and usr_info:
            # Get ticket by key
            try:
                ticket = ndb.Key(urlsafe=id).get()
            except KeyError:
                self.redirect("/error?msg=key " + id + " does not exist")
                return

            ticket.title = self.request.get("title", "").strip()
            ticket.desc = self.request.get("desc", "").strip()
            ticket.client_email = self.request.get("client_email", "").strip()
            ticket.classroom = self.request.get("classroom", "").strip()
            ticket.progress = Ticket.Progress.value_from_str(self.request.get("progress"))
            ticket.status = Ticket.Status.value_from_str(self.request.get("status"))
            ticket.priority = Ticket.Priority.value_from_str(self.request.get("priority"))
            ticket.type = Ticket.Type.value_from_str(self.request.get("type"))

            if (not ticket.client_email
                    and usr_info.is_client()):
                ticket.client_email = usr_info.email

            # Chk
            if len(ticket.title) < 1:
                self.redirect("/error?msg=Aborted modification: missing title")
                return

            if len(ticket.desc) < 1:
                self.redirect("/error?msg=Aborted modification: missing desc")
                return

            # Report
            tickets.send_email_for(ticket, "modified", "    modified by: " + unicode(usr_info))

            # Save
            ticket.born = True
            tickets.update(ticket)
            self.redirect("/info?url=/manage_tickets&msg=Ticket modified: "
                          + ticket.title.encode("ascii", "replace"))
        else:
            self.redirect("/")


app = webapp2.WSGIApplication([
    ("/tickets/modify", ModifyTicket),
], debug=True)
