#!/usr/bin/env python
# coding: utf-8
# (c) Baltasar 2018 MIT License <baltasarq@gmail.com>


import webapp2
from google.appengine.api import users
from webapp2_extras import jinja2
import logging as logs
import model.user as usr_mgt
import model.ticket as tickets
from model.ticket import Ticket
from model.appinfo import AppInfo


class AddToner(webapp2.RequestHandler):
    def get(self):
        usr = users.get_current_user()
        usr_info = usr_mgt.retrieve(usr)

        if usr and usr_info:
            access_link = users.create_logout_url("/")

            template_values = {
                "info": AppInfo,
                "usr_info": usr_info,
                "access_link": access_link,
            }

            jinja = jinja2.get_jinja2(app=self.app)
            self.response.write(jinja.render_template("toner.html", **template_values))
        else:
            self.redirect("/")

    def post(self):
        user = users.get_current_user()
        usr_info = usr_mgt.retrieve(user)

        if user and usr_info:
            # Retrieve values
            cartridge_model = self.request.get("cartridge_model", "").strip()
            printer_maker = self.request.get("printer_maker", "").strip()
            printer_model = self.request.get("printer_model", "").strip()
            str_num_units = self.request.get("number_of_units", "").strip()
            client = self.request.get("client", "").strip()
            client_email = self.request.get("client_email", "").strip()
            num_units = 1

            # Chk
            if len(cartridge_model) < 3:
                self.redirect("/error?msg=Aborted modification: missing cartridge model")
                return

            if len(printer_maker) < 2:
                self.redirect("/error?msg=Aborted modification: missing printer maker")
                return

            if len(printer_model) < 5:
                self.redirect("/error?msg=Aborted modification: missing printer model")
                return

            try:
                num_units = int(str_num_units)
            except ValueError:
                logs.error("Invalid number of units: " + str_num_units)

            if (num_units < 1
               or num_units > 10):
                logs.error("Invalid number of units (1 < units < 10): " + str_num_units)

            # Create ticket
            ticket = tickets.create(usr_info)

            ticket.born = True
            ticket.progress = Ticket.Progress.Tracked
            ticket.status = Ticket.Status.Open
            ticket.priority = Ticket.Priority.Low
            ticket.type = Ticket.Type.Supplies

            ticket.title = u"Toner: " + printer_maker\
                           + u" " + printer_model\
                           + u" " + cartridge_model
            ticket.desc = u"Client: " + client + u"\nInk cartridge requested for: "\
                          + printer_maker + " " + printer_model + '\n'\
                          + u"Cartridge #" + cartridge_model + "\n"\
                          + unicode(num_units) + u" units"
            ticket.client_email = client_email
            ticket.classroom = ""

            # Report
            tickets.send_email_for(ticket, "Ink cartridge request", "    by " + unicode(usr_info))

            # Save
            tickets.update(ticket)
            self.redirect("/info?url=/manage_tickets&msg=Ink cartridge requested: "
                          + ticket.title.replace('#', '').encode("ascii", "replace"))
        else:
            self.redirect("/")


app = webapp2.WSGIApplication([
    ("/tickets/toner", AddToner),
], debug=True)
