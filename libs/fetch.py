# ~/~ begin <<docs/gong-web-app/fetch-courses.md#libs/fetch.py>>[init]
import requests
import pandas as pd
import json
from tabulate import tabulate
from datetime import datetime, date, timedelta
from fasthtml.common import *

from libs.utils import add_months_days
from libs.dbset import get_db_path

# Example usage:
# fetch_dhamma_courses("Mahi", 6, 0)
# fetch_dhamma_courses("Pajjota", 6, 0)

def get_field_from_db(db_central, center_name, field_name):
    # get the dhamma.org location for this center from the table settings in center db
    centers = db_central.t.centers
    Center = centers.dataclass()
    if field_name == "location":
        location = centers[center_name].location
        return f"location_{location}"
    else:
        other_course = centers[center_name].other_course
        return json.loads(other_course)

def fetch_courses_from_dhamma(location, date_start, date_end):
    url = "https://www.dhamma.org/en-US/courses/do_search"
    headers = {"User-Agent": "entan-mkdocs-fetcher/1.0"}
    all_courses = []

    # Initial page
    page = 1

    while True:
        data = {
            "current_state": "OldStudents",
            "regions[]": location,
            "daterange": f"{date_start} - {date_end}",
            "page": str(page),
        }

        print(f"Fetching courses Dhamma {location} - Page {page}...")
        try:
            resp = requests.post(url, data=data, headers=headers, timeout=15)
            resp.raise_for_status()
            payload = resp.json()
        except requests.RequestException as e:
            print("Request error:", e)
            return []
        except ValueError as e:
            print("Invalid JSON:", e)
            return []

        courses = payload.get("courses", [])
        all_courses.extend(courses)

        # Check if there are more pages
        total_pages = payload.get("pages", 0)
        if page >= total_pages:
            break

        page += 1

    # Extract relevant fields from all courses
    extracted = [
        {
            "course_start_date": c.get("course_start_date"),
            "course_end_date": c.get("course_end_date"),
            "raw_course_type": c.get("raw_course_type"),
            "course_type_anchor": c.get("course_type_anchor"),
            "course_type": c.get("course_type"),
            "sub_location": c.get("location", {}).get("sub_location"),
            "center_non": c.get("location", {}).get("center_noncenter"),
        }
        for c in all_courses
    ]

    # Filter out extracted where 'center_non' = 'noncenter'
    extracted = [course for course in extracted if course['center_non'] != 'noncenter']

    return extracted

def get_period_type(anchor, course_type, list_of_types, other_dict):
    """
    If anchor == "Other", find in other_dict the value of a key == course_type
    and return "UNKNOWN" if not found.
    if anchor != "Other"' find the dict in list_of_types where 'raw_course_type' matches anchor and return the value of 'period_type'.
    """
    if anchor == "Other":
        return other_dict.get(course_type.upper(), "UNKNOWN")
    else:    
        for item in list_of_types:
            if  anchor == item.get('raw_course_type'):
                return item.get('period_type')
    return "UNKNOWN"

def deduplicate(merged):
    # Remove duplicates: if consecutive items have identical start_date and period_type,
    # keep only one with source='BOTH'
    deduplicated = []
    i = 0
    while i < len(merged):
        current = merged[i]
        if i + 1 < len(merged):
            next_item = merged[i + 1]
            if (current['start_date'] == next_item['start_date'] and 
                current['period_type'] == next_item['period_type']):
                # Mark as BOTH and skip the next one
                current['source'] = 'BOTH'
                deduplicated.append(current)
                i += 2  # skip next item
                continue
        deduplicated.append(current)
        i += 1
    return deduplicated

def fetch_dhamma_courses(center, num_months, num_days):

    # get the path to the center db and the spreadsheet (see below)
    db_path = get_db_path()

    db_center = database(f"{db_path}{center.lower()}.ok.db")
    db_central = database(f"{db_path}gongUsers.db")

    # get the start date for the last course just before today = current course - or service
    periods = db_center.t.coming_periods
    Period = periods.dataclass()
    count_past = sum(1 for item in periods() if date.fromisoformat(item.start_date) < date.today())
    date_current_course = periods()[count_past-1].start_date

    # get a dict. of all courses in the center db starting from the current course
    periods_db_center_obj = periods()[count_past-1:]
    periods_db_center = [
    {
        'start_date': p.start_date,
        'period_type': p.period_type,
        'source' : f"{center.lower()}_db"

    }
    for p in periods_db_center_obj
    ]

    location = get_field_from_db(db_central, center, "location")
    end_date = add_months_days(date_current_course, num_months, num_days)

    # fetch extracted courses from dhamma.org
    extracted = fetch_courses_from_dhamma(location, date_current_course, end_date)

    # FIXME one day courses are possible in some centers !!!
    extracted = [course for course in extracted if not course['raw_course_type'].startswith("1-Day")]

    # Remove the last two fields: 'sub_location' and 'center_non'
    for course in extracted:
        course.pop('sub_location', None)
        course.pop('center_non', None)
        # Remove "OSC" suffix from 'raw_course_type' and 'course_type_anchor' if present
        # if course['raw_course_type'].endswith("OSC"):
        #      course['raw_course_type'] = course['raw_course_type'][:-3].strip()
        if course['course_type_anchor'].endswith("OSC"):
            course['course_type_anchor'] = course['course_type_anchor'][:-3].strip()

    # print(tabulate(extracted, headers="keys", tablefmt="grid"))

    # get the course_type mapping table from the spreadsheet
    # and use it to map the course types from dhamma.org to center db
    df = pd.read_excel(db_path + 'course_type_map.xlsx')
    list_of_types = df.to_dict(orient='records')
    other_dict = get_field_from_db(db_central, center, "other_dict")
    periods_dhamma_org = [
        {
            "start_date": c.get("course_start_date"),
            "period_type": get_period_type(c.get("course_type_anchor"), c.get("course_type"), list_of_types, other_dict),
            "source": "dhamma.org",
            "course_type": c.get("course_type")
        }
        for c in extracted
    ]

    # print(tabulate(periods_dhamma_org, headers="keys", tablefmt="grid"))
    # print(tabulate(periods_db_center, headers="keys", tablefmt="grid"))

    merged = periods_db_center + periods_dhamma_org
    mer_sort = sorted (merged,key=lambda x: x['start_date'])
    deduplicated = deduplicate(mer_sort)

    print(tabulate(deduplicated, headers="keys", tablefmt="grid"))
    return
# ~/~ end
