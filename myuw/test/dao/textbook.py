from django.test import TestCase
from myuw.dao.schedule import _get_schedule
from restclients.models import Term
from restclients.exceptions import DataFailureException
from myuw.dao.textbook import get_textbook_by_schedule
from myuw.dao.textbook import get_verba_link_by_schedule


class TestTextbooks(TestCase):
    def test_get_by_schedule(self):
        regid = "9136CCB8F66711D5BE060004AC494FFE"
        term = Term()
        term.year = 2012
        term.quarter = "summer"
        schedule = _get_schedule(regid, term)

        books = get_textbook_by_schedule(schedule)
        self.assertEquals(len(books), 1)
        self.assertEquals(books["13833"][0].title,
                          "2 P/S Tutorials In Introductory Physics")

    def test_get_verba_by_schedule(self):
        regid = "9136CCB8F66711D5BE060004AC494FFE"
        term = Term()
        term.year = 2013
        term.quarter = "spring"
        schedule = _get_schedule(regid, term)

        returned_link = get_verba_link_by_schedule(schedule)

        expected_link = ("http://uw-seattle.verbacompare.com/m?"
                         "section_id=AB12345&quarter=spring")
        self.assertEquals(returned_link, expected_link)

        regid = "9136CCB8F66711D5BE060004AC494FFE"
        term = Term()
        term.year = 2014
        term.quarter = "winter"
        schedule = _get_schedule(regid, term)
        self.assertRaises(DataFailureException,
                          get_verba_link_by_schedule,
                          schedule)
