# ~/~ begin <<docs/obtain-schedule/python-code.md#zkeep/fetch-courses.py>>[init]
import requests
import pandas as pd
import calendar
from tabulate import tabulate
from datetime import datetime, date
from fasthtml.common import *

def get_location_from_db(db_central, center_name):
    # get the dhamma.org location for this center from the table settings in center db
    centers = db_central.t.centers
    Center = centers.dataclass()
    location = centers[center_name].location
    return f"location_{location}"

def add_months(date_str, num_months):
    """
    Return an ISO date string num_months after date_str (YYYY-MM-DD).
    Uses divmod to compute year/month rollover and preserves end-of-month.
    """
    dt = datetime.strptime(date_str, "%Y-%m-%d").date()
    # total months since year 0 (make month zero-based)
    total = dt.year * 12 + (dt.month - 1) + num_months
    new_year, new_month0 = divmod(total, 12)
    new_month = new_month0 + 1
    last_day = calendar.monthrange(new_year, new_month)[1]
    new_day = min(dt.day, last_day)
    return date(new_year, new_month, new_day).isoformat()

def get_period_type(raw_course_type, course_type, list_of_types):
    """
    Find the dict in list_of_types where 'raw_course_type' matches arg1
    and return the value of 'period_type' if:
    - arg1 != "Other"
    - arg1 == "Other" and arg2 in 'course_type'
    and return "UNKNOWN" if not found.
    """
    for item in list_of_types:
        if  raw_course_type == item.get('raw_course_type'):
            if raw_course_type == "Other":
                if course_type in item.get("course_type"):
                    return item.get('period_type')    
            else:
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

def fetch_dhamma_courses(center, num_months):

    # get the path to the center db and the spreadsheet (see below)
    db_path = "" # if isa_dev_computer() else os.environ.get('RAILWAY_VOLUME_MOUNT_PATH',"None") + "/"

    db_center = database(f"{db_path}data/{center.lower()}.ok.db")
    db_central = database(f"{db_path}data/gongUsers.db")

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

    location = get_location_from_db(db_central, center)
    end_date = add_months(date_current_course, num_months)


    url = "https://www.dhamma.org/en-US/courses/do_search"
    headers = {"User-Agent": "entan-mkdocs-fetcher/1.0"}
    all_courses = []

    # Initial page
    page = 1

    while True:
        data = {
            "current_state": "OldStudents",
            "regions[]": location,
            "daterange": f"{date_current_course} - {end_date}",
            "page": str(page),
        }

        print(f"Fetching courses Dhamma {center} - Page {page}...")
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

    # print intermediary data
    # print(tabulate(extracted, headers="keys", tablefmt="grid"))

    # Filter out extracted where 'center_non' = 'noncenter'
    extracted = [course for course in extracted if course['center_non'] != 'noncenter']

    # Filter out extracted for 1-Day courses
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
    df = pd.read_excel(db_path + 'data/course_type_map.xlsx')
    list_of_types = df.to_dict(orient='records')
    periods_dhamma_org = [
        {
            "start_date": c.get("course_start_date"),
            "period_type": get_period_type(c.get("course_type_anchor"), c.get("course_type"), list_of_types),
            "source": "dhamma.org",
            "course_type": c.get("course_type")
        }
        for c in extracted
    ]

    # print(tabulate(periods_dhamma_org, headers="keys", tablefmt="grid"))
    # print(tabulate(periods_db_center, headers="keys", tablefmt="grid"))

    merged = periods_db_center + periods_dhamma_org
    merged.sort(key=lambda x: x['start_date'])

    deduplicated = deduplicate(merged)

    print(tabulate(deduplicated, headers="keys", tablefmt="grid"))
    return

# Example usage:
if __name__ == "__main__":
    fetch_dhamma_courses("Mahi", 6)
    fetch_dhamma_courses("Pajjota", 6)
# ~/~ end
