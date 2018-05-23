# infra-esei-tickets (c) Baltasar 2018 MIT License <baltasarq@gmail.com>

import webapp2
from google.appengine.api import users
from model.ticket import Ticket
import model.user as usr_mgt


class TonerReportManager(webapp2.RequestHandler):
    def add_csv_row(self, ticket):
        """Called when one row is going to be added to the csv document."""
        new_row = '"' + ticket.title + '"'
        new_row += ',"' + ticket.desc.replace('\n', '  ') + '"'
        new_row += ',"' + ticket.client_email + '"'
        self.csv_content += new_row + "\n"

    def get(self):
        user = users.get_current_user()
        usr_info = usr_mgt.retrieve(user)
        
        if user and usr_info and usr_info.is_admin():
            self.csv_content = ""
            tickets = Ticket.query(Ticket.type == Ticket.Type.Supplies).order(-Ticket.added)
            tickets.map(self.add_csv_row)

            self.response.headers['Content-Type'] = "text/csv"
            self.response.headers['Content-Disposition'] = "attachment; filename=supplies.csv"
            self.response.write(self.csv_content)
        else:
            self.redirect("/")
            return


app = webapp2.WSGIApplication([
    ('/tickets/toner_report', TonerReportManager),
], debug=True)
