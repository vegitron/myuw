from django.http import HttpResponse
import logging
from operator import itemgetter
from django.utils import simplejson as json
from myuw_mobile.dao.building import get_buildings_by_schedule
from myuw_mobile.dao.canvas import get_canvas_enrolled_courses
from myuw_mobile.dao.course_color import get_colors_by_schedule
from myuw_mobile.dao.schedule import get_schedule_by_term
from myuw_mobile.dao.schedule import filter_schedule_sections_by_summer_term
from myuw_mobile.dao.registered_term import get_current_summer_term_in_schedule
from myuw_mobile.logger.logresp import log_data_not_found_response
from myuw_mobile.logger.logresp import log_success_response
from myuw_mobile.views.rest_dispatch import RESTDispatch, data_not_found


class StudClasSche(RESTDispatch):

    def make_http_resp (self, logger, timer, term, summer_term=None):
        if term is None:
            log_data_not_found_response(logger, timer)
            return data_not_found()

        schedule = get_schedule_by_term(term)
        if schedule is None:
            log_data_not_found_response(logger, timer)
            return data_not_found()

        if not schedule.json_data():
            log_data_not_found_response(logger, timer)
            return HttpResponse({})

        if summer_term is None:
            summer_term = get_current_summer_term_in_schedule(schedule)

        resp_data = load_schedule(schedule, summer_term)
        if resp_data is None:
            log_data_not_found_response(logger, timer)
            return data_not_found()

        log_success_response(logger, timer)
        return HttpResponse(json.dumps(resp_data))


def load_schedule(schedule, summer_term=""):
    filter_schedule_sections_by_summer_term(schedule, summer_term)

    colors = get_colors_by_schedule(schedule)
    if colors is None and len(schedule.sections) > 0:
        return None

    buildings = get_buildings_by_schedule(schedule)

    canvas_data_by_course_id = get_canvas_enrolled_courses()

    # Since the schedule is restclients, and doesn't know
    # about color ids, backfill that data
    json_data = schedule.json_data()
    
    section_index = 0
    for section in schedule.sections:
        section_data = json_data["sections"][section_index]
        color = colors[section.section_label()]
        section_data["color_id"] = color
        section_index += 1

        if section.section_label() in canvas_data_by_course_id:
            enrollment = canvas_data_by_course_id[section.section_label()]
            canvas_url = enrollment.course_url
            canvas_name = enrollment.course_name
            canvas_grade = enrollment.final_grade
            section_data["canvas_url"] = canvas_url
            section_data["canvas_name"] = canvas_name
            section_data["canvas_grade"] = canvas_grade

        # MUWM-596
        if section.final_exam and section.final_exam.building:
            building = buildings[section.final_exam.building]
            if building:
                section_data["final_exam"]["longitude"] = building.longitude
                section_data["final_exam"]["latitude"] = building.latitude
                section_data["final_exam"]["building_name"] = building.name

        # Also backfill the meeting building data
        meeting_index = 0
        for meeting in section.meetings:
            mdata = section_data["meetings"][meeting_index]
            if not mdata["building_tbd"]:
                building = buildings[mdata["building"]]
                if building is not None:
                    mdata["latitude"] = building.latitude
                    mdata["longitude"] = building.longitude
                    mdata["building_name"] = building.name

            for instructor in mdata["instructors"]:
                if not instructor[
                    "email1"] and not instructor[
                    "email2"] and not instructor[
                    "phone1"] and not instructor[
                    "phone2"] and not instructor[
                    "voicemail"] and not instructor[
                    "fax"] and not instructor[
                    "touchdial"] and not instructor[
                    "address1"] and not instructor[
                    "address2"]:
                    instructor["whitepages_publish"] = False
            meeting_index += 1

    # MUWM-443
    json_data["sections"] = sorted(json_data["sections"],
                                   key=itemgetter('curriculum_abbr',
                                                  'course_number',
                                                  'section_id',
                                                  ))
    json_data["summer_term"]=summer_term
    return json_data