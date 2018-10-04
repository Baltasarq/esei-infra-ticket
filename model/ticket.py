#!/usr/bin/env python
# coding: utf-8
# (c) Baltasar 2018 MIT License <baltasarq@gmail.com>


from google.appengine.runtime.apiproxy_errors import OverQuotaError
from google.appengine.api.mail import EmailMessage
from google.appengine.ext import ndb
import datetime as dt
import logging

from model.enums import Enum

from model.appinfo import AppInfo


class Comment(ndb.Model):
    author = ndb.TextProperty(indexed=True)
    text = ndb.TextProperty()


class Ticket(ndb.Model):
    Progress = Enum([
        "New", "Stalled", "Tracked",
        "Fixed", "Inappropriate", "Impossible"])

    Status = Enum(["Open", "Closed"], start=100)
    Priority = Enum(["Low", "Normal", "High"], start=200)
    Type = Enum(["Repair", "Printer", "Software", "Supplies"], start=300)

    serial = ndb.IntegerProperty(indexed=True, required=True)
    added = ndb.DateProperty(auto_now_add=True, indexed=True)
    title = ndb.TextProperty(indexed=True, required=True)
    owner_email = ndb.TextProperty(indexed=True, required=True)
    client_email = ndb.TextProperty(indexed=True)
    desc = ndb.TextProperty(required=True)
    progress = ndb.IntegerProperty(indexed=True)
    status = ndb.IntegerProperty(indexed=True)
    priority = ndb.IntegerProperty(indexed=True)
    type = ndb.IntegerProperty(indexed=True)
    classroom = ndb.TextProperty(indexed=True)
    comments = ndb.StructuredProperty(Comment, repeated=True)
    born = ndb.BooleanProperty()

    def get_status_attributes(self):
        return "|" + Ticket.Type.values[self.type] + " "\
                + Ticket.Priority.values[self.priority] + " "\
                + Ticket.Progress.values[self.progress] + " "\
                + Ticket.Status.values[self.status] + "|"

    def __str__(self):
        return "#" + str(self.serial) + " " + self.title.encode("ascii", "replace")\
                + '\n' + str(self.added).encode("ascii", "replace")\
                + " (" + self.owner_email.encode("ascii", "replace") + ") "\
                + (" -> " + self.client_email.encode("ascii", "replace") if self.client_email else "")\
                + (" @ " + self.classroom.encode("ascii", "replace") if self.classroom else "")\
                + "\n" + self.get_status_attributes()\
                + "\n\n'" + self.desc.encode("ascii", "replace") + "'"

    def __unicode__(self):
        return "#" + unicode(self.serial) + " " + self.title \
                + u'\n' + unicode(self.added) \
                + u" (" + unicode(self.owner_email) \
                + (u" -> " + unicode(self.client_email) if self.client_email else u"") \
                + (u" @ " + unicode(self.classroom) if self.classroom else u"") \
                + u"\n" + unicode(self.get_status_attributes()) \
                + u"\n\n'" + unicode(self.desc) + u"'"


def create_open_tickets_query_for_email(email):
    """Creates a query to retrieve relevant open tickets for a client."""

    email = email.strip()

    return Ticket.query(Ticket.born == True
                        and Ticket.status == Ticket.Status.Open
                        and (Ticket.owner_email == email
                             or Ticket.client_email == email))


def create_query_for_email(email):
    """Creates a query to retrieve relevant tickets for a client."""

    email = email.strip()

    return Ticket.query(Ticket.born == True
                        and Ticket.owner_email == email
                        or Ticket.client_email == email)


def create_query_all():
    """Creates a query to retrieve all tickets."""

    return Ticket.query(Ticket.born == True)


def create_open_tickets_query_all():
    """Creates a query to retrieve all open tickets."""

    return Ticket.query(Ticket.born == True and Ticket.status == Ticket.Status.Open)


def create(user):
    """Creates a new ticket, given the author's user.

    :param user: The User (not GAE's user object) object.
    :return: A new Ticket object.
    """
    now = dt.datetime.today()
    num_tickets = Ticket.query(Ticket.added == now).count() + 1
    toret = Ticket()

    toret.serial = int(unicode.format(
                        u"{0:04d}{1:02d}{2:02d}{3:02d}",
                        now.year, now.month, now.day, num_tickets))
    toret.title = "Big problem #" + unicode(num_tickets)
    toret.owner_email = user.email
    toret.client_email = ""
    toret.classroom = ""
    toret.desc = "Write a meaningful description of the problem, " \
                 "also the steps to reproduce it."
    toret.progress = Ticket.Progress.New
    toret.status = Ticket.Status.Open
    toret.type = Ticket.Type.Repair
    toret.priority = Ticket.Priority.Low
    toret.born = False

    return toret


def clean_unborn():
    """Removes asynchronously those tickets that
       technically were created but never modified for the first time."""

    # Makes me sick, but ndb only understands == True or == False
    unborn_ticket_keys = Ticket.query(Ticket.born == False).fetch(keys_only=True)
    ndb.delete_multi_async(unborn_ticket_keys)


def send_email_chk_for(ticket, subject, body):
    send_std_email_for(ticket, subject, unicode(ticket.get_status_attributes()) + u"\n\n" + body)


def send_email_for(ticket, subject, body):
    send_std_email_for(ticket, subject, unicode(ticket) + u'\n' + body)


def send_std_email_for(ticket, subject, body):
    body = unicode(dt.datetime.today().strftime("%Y-%m-%d %H:%M:%S")) \
           + u"\nrcpts: " + AppInfo.BroadcastEmail\
           + (u", " + ticket.client_email if ticket.client_email else u"") \
           + u'\n\n' + body \
           + u"\n\n---\n\n" + AppInfo.AppWeb + u'\n'

    subject = subject.strip().lower()
    subject = subject[0].upper() + subject[1:]
    subject = subject + u" ticket #" + unicode(ticket.serial) \
            + ' ' + ticket.title

    send_email(AppInfo.BroadcastEmail, subject, body)
    if ticket.client_email:
        send_email(ticket.client_email, subject, body)


def send_email(rcpt, subject, body):
    subject = subject
    body = body

    logging.debug("Sending mail: '" + subject + "' to: " + rcpt)

    try:
        EmailMessage(
            sender=AppInfo.AppEmail,
            subject=subject,
            to=rcpt,
            body=body).send()
        logging.debug("Email sent: '" + subject + "' to: " + rcpt)
    except OverQuotaError as e:
        logging.error("Quota error sending mail: '" + subject + "' to: " + rcpt
                      + "\n\t" + e.message)
    except Exception as e:
        logging.error("Unexpected error sending mail: '" + subject + "' to: " + rcpt
                      + "\n\t" + e.message)


@ndb.transactional
def update(ticket):
    """Updates a section.

        :param par: The ticket to update.
        :return: The key of the record.
    """
    return ticket.put()
