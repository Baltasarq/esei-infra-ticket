#!/usr/bin/env python
# coding: utf-8
# (c) Baltasar 2018 MIT License <baltasarq@gmail.com>


import webapp2
from google.appengine.api import users
from google.appengine.ext import ndb
from webapp2_extras import jinja2

import model.ticket as tickets
from model.ticket import Ticket
import model.user as usr_mgt
from model.appinfo import AppInfo


class ChkTicket(webapp2.RequestHandler):
    MinCommentLength = 10

    def get(self):
        try:
            id = self.request.GET['ticket_id']
        except:
            self.redirect("/error?msg=ticket was not found")
            return

        usr = users.get_current_user()
        usr_info = usr_mgt.retrieve(usr)

        if usr and usr_info:
            access_link = users.create_logout_url("/")

            try:
                ticket = ndb.Key(urlsafe=id).get()
            except:
                self.redirect("/error?msg=key " + id + " does not exist")
                return

            if (usr_info.email != ticket.owner_email
            and usr_info.is_client()):
                self.redirect("/error?msg=User " + usr_info.email + " not allowed to check tickets")
                return

            template_values = {
                "info": AppInfo,
                "usr_info": usr_info,
                "access_link": access_link,
                "ticket": ticket,
                "comments": ticket.comments,
                "Status": Ticket.Status,
                "Progress": Ticket.Progress,
                "Priority": Ticket.Priority,
                "Type": Ticket.Type,
                "MinCommentLength": ChkTicket.MinCommentLength
            }

            jinja = jinja2.get_jinja2(app=self.app)
            self.response.write(jinja.render_template("chk_ticket.html", **template_values))
        else:
            self.redirect("/")

    def post(self):
        try:
            id = self.request.GET['ticket_id']
        except:
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
            except:
                self.redirect("/error?msg=key #" + id + " does not exist")
                return

            if (usr_info.email != ticket.owner_email
            and usr_info.is_client()):
                self.redirect("/error?msg=User " + user.email + " not allowed to check tickets")
                return

            new_comment = self.request.get("comment", "").strip()

            if len(new_comment) >= ChkTicket.MinCommentLength:
                ticket.client_email = self.request.get("client_email", "").strip()
                ticket.classroom = self.request.get("classroom", "").strip()
                ticket.progress = Ticket.Progress.value_from_str(self.request.get("progress"))
                ticket.status = Ticket.Status.value_from_str(self.request.get("status"))
                ticket.comments.append(tickets.Comment(author=usr_info.email, text=new_comment))

                # Report
                tickets.send_email_chk_for(ticket, "checked", usr_info.email + " says:\n" + new_comment)

                # Save
                tickets.update(ticket)
                self.redirect("/info?url=/manage_tickets&msg=Ticket checked: "
                              + ticket.Status.values[ticket.status]
                              + " " + ticket.Progress.values[ticket.progress]
                              + " " + ticket.title.encode("ascii", "replace"))
            else:
                self.redirect("/error?msg=Comment should be at least of "
                              + unicode(ChkTicket.MinCommentLength) + " chars.")
        else:
            self.redirect("/")


app = webapp2.WSGIApplication([
    ("/tickets/chk", ChkTicket),
], debug=True)
