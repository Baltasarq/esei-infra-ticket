# infra-esei-tickets (c) Baltasar 2018 MIT License <baltasarq@gmail.com>

import webapp2
from webapp2_extras import jinja2
from google.appengine.api import users
from google.appengine.ext import ndb

from model.appinfo import AppInfo
from model.ticket import Ticket
import model.ticket as ticket_mgt
import model.user as usr_mgt


class TicketsManager(webapp2.RequestHandler):
    MAX_TICKETS_PER_PAGE = 12
    NUM_PAGES_SHOWN = 10

    def filter_by_search_terms(self, ticket):
        title = ticket.title.strip().lower()
        desc = ticket.desc.strip().lower()

        for search_term in self.list_search_terms:
            search_term = search_term

            if (title.find(search_term) >= 0
               or desc.find(search_term) >= 0):
                self.ticket_key_set.append(ticket.key)
                break

        return

    @staticmethod
    def paginate(tickets, pages_info, current_page):
        """Paginates the results in self.tickets, and self.pages_info"""
        page_buttons_each_side = TicketsManager.MAX_TICKETS_PER_PAGE // 2
        num_tickets = len(tickets)
        num_pages = (num_tickets // TicketsManager.MAX_TICKETS_PER_PAGE) + 1
        current_page = min(num_pages - 1, max(0, current_page))

        pages_info["current"] = current_page
        pages_info["previous"] = max(0, current_page - 1)
        pages_info["last"] = num_pages - 1
        pages_info["next"] = min(num_pages - 1, current_page + 1)
        pages_info["relevant"] = range(max(0, current_page - page_buttons_each_side),
                                       min(num_pages - 1, current_page + page_buttons_each_side) + 1)

        first_ticket = current_page * TicketsManager.MAX_TICKETS_PER_PAGE
        last_ticket = first_ticket + TicketsManager.MAX_TICKETS_PER_PAGE
        tickets = tickets[first_ticket:last_ticket]
        return ndb.get_multi_async(tickets)

    def get(self):
        try:
            arg_show_all = self.request.GET['show_all']
        except KeyError:
            arg_show_all = "false"

        try:
            arg_page = int(self.request.GET['page'])
        except KeyError or ValueError:
            arg_page = 0

        try:
            arg_search_terms = self.request.GET['search']
        except KeyError:
            arg_search_terms = ""

        show_all = (arg_show_all == "true")
        self.list_search_terms = [x.lower() for x in arg_search_terms.strip().split()]
        pages_info = {}

        user = users.get_current_user()
        usr_info = usr_mgt.retrieve(user)
        
        if user and usr_info:
            ticket_mgt.clean_unborn()
            access_link = users.create_logout_url("/")

            # Retrieve the relevant tickets
            # This could be made shorter, but I prefer to access the db
            # with a query as limited as possible
            if usr_info.is_client():
                if not show_all:
                    tickets = ticket_mgt.create_open_tickets_query_for_email(usr_info.email)
                else:
                    tickets = ticket_mgt.create_query_for_email(usr_info.email)
            else:
                if not show_all:
                    tickets = ticket_mgt.create_open_tickets_query_all()
                else:
                    tickets = ticket_mgt.create_query_all()

            tickets = tickets.order(-Ticket.added)
            if self.list_search_terms:
                self.ticket_key_set = []
                tickets.map(self.filter_by_search_terms)
                tickets = self.ticket_key_set
            else:
                tickets = tickets.fetch(keys_only=True)

            future_tickets = TicketsManager.paginate(tickets, pages_info, arg_page)

            template_values = {
                "info": AppInfo,
                "access_link": access_link,
                "Status": Ticket.Status,
                "Priority": Ticket.Priority,
                "Progress": Ticket.Progress,
                "usr_info": usr_info,
                "show_all": show_all,
                "search_terms": arg_search_terms,
                "pages_info": pages_info
            }

            jinja = jinja2.get_jinja2(app=self.app)
            tickets = [x.get_result() for x in future_tickets]
            template_values["tickets"] = tickets
            self.response.write(jinja.render_template("tickets.html", **template_values))
        else:
            self.redirect("/")
            return


app = webapp2.WSGIApplication([
    ('/manage_tickets', TicketsManager),
], debug=True)
