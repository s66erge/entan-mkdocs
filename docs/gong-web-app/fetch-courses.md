# Get schedule from dhamma.org and merge into center schedule

### Example usage:
fetch_dhamma_courses("Mahi", 6, 0)
fetch_dhamma_courses("Pajjota", 6, 0)

```{.python file=libs/fetch.py}
import requests
import pandas as pd
import json
from datetime import date
from fasthtml.common import *

from libs.utils import add_months_days
from libs.dbset import get_db_path, get_central_db

<<field-fr-db>>
<<fetch-api>>
<<period-type>>
<<deduplicate>>
<<fetch-courses>>
```

Get the dhamma.org location for this center from the table settings in center db

```{.python #field-fr-db}

def get_field_from_db(db_central, center_name, field_name):
    centers = db_central.t.centers
    Center = centers.dataclass()
    if field_name == "location":
        location = centers[center_name].location
        return f"location_{location}"
    else:
        other_course = centers[center_name].other_course
        return json.loads(other_course)
```

Get the courses from www.dhamma.org for a specific center from date_start until date_end, keep only the relevant fields for courses inside the center.

```{.python #fetch-api}

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

    # Extract relevant fields from courses located inside the center
    # Filter out where 'center_non' = 'noncenter'
    extracted = [
        {
            "course_start_date": c.get("course_start_date"),
            "course_end_date": c.get("course_end_date"),
            "raw_course_type": c.get("raw_course_type"),
            "course_type_anchor": c.get("course_type_anchor"),
            "course_type": c.get("course_type"),
            "sub_location": c.get("location", {}).get("sub_location"),
            # "center_non": c.get("location", {}).get("center_noncenter"),
        }
        for c in all_courses if c.get("location", {}).get("center_noncenter") != 'noncenter'
    ]
    return extracted
```

If anchor == "Other", find in other_dict the value of a key == course_type
and return "UNKNOWN" if not found.
if anchor != "Other"' find the dict in list_of_types where 'raw_course_type' matches anchor and return the value of 'period_type'.

```{.python #period-type}

def get_period_type(anchor, course_type, list_of_types, other_dict):
    if anchor == "Other":
        return other_dict.get(course_type.upper(), "UNKNOWN")
    else:    
        for item in list_of_types:
            if  anchor == item.get('raw_course_type'):
                return item.get('period_type')
    return "UNKNOWN"
```

Remove duplicates: if consecutive items have identical start_date and period_type,
keep only one with source='BOTH'

```{.python #deduplicate}
def deduplicate(merged):
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

def check_plan(plan, db_center):
    try:
        # build set of all period_types in db_center.t.periods_struct
        periods_struct = db_center.t.periods_struct()
        valid_types = {row.get("period_type") for row in periods_struct}
    except Exception:
        valid_types = set()
    for item in plan:
        pt = item.get("period_type")
        if pt in valid_types:
            item["check"] = "OK"
        else:
            item["check"] = "NoType"

    for idx, item in enumerate(plan[:-1]):
        type_check = item.get("check")
        if type_check.startswith("OK"):
            pt = item.get("period_type")
            try:
                # Fetch periods_struct with matching period_type
                periods_struct_rows = [row for row in db_center.t.periods_struct() if row.get("period_type") == pt]
                # Find the biggest 'day' value
                max_day = max((row.get("day") for row in periods_struct_rows if row.get("day") is not None), default=None)
            except Exception:
                max_day = None

            # Get this and next start_date as date objects
            start_date_1 = item.get("start_date")
            start_date_2 = plan[idx + 1].get("start_date")
            try:
                d1 = date.fromisoformat(start_date_1)
                d2 = date.fromisoformat(start_date_2)
                number_of_days = (d2 - d1).days
            except Exception:
                # If missing or invalid, skip to next
                continue

            if max_day is not None:
                if number_of_days < max_day:
                    item["check"] = f"Nok-{max_day}"
        else:
            item["check"] += "|???"

    return plan
```

Get a merged list of courses from the current courses in the center db and the future courses in dhamma.org:
- from the start of the current course/service until num_months plus num_days days in th future 
- course types mapped to the courses databases courses
- with a source field "dhamma.org", "center db" or "BOTH"

```{.python #fetch-courses}

def fetch_dhamma_courses(center, num_months, num_days):

    db_path = get_db_path()  ## [1]
    db_central = get_central_db()
    centers = db_central.t.centers
    Center = centers.dataclass()
    selected_db = centers[center].gong_db_name
    db_center = database(db_path + selected_db)

    periods = db_center.t.coming_periods
    Period = periods.dataclass()
    count_past = sum(1 for item in periods() if date.fromisoformat(item.start_date) < date.today())
    date_current_course = periods()[count_past-1].start_date  ## [2]

    periods_db_center_obj = periods()[count_past-1:]  ## [3]
    periods_db_center = [
    {
        'start_date': p.start_date,
        'period_type': p.period_type,
        'source' : f"{center.lower()}_db"

    }
    for p in periods_db_center_obj  ## [3]
    ]

    location = get_field_from_db(db_central, center, "location")
    end_date = add_months_days(date_current_course, num_months, num_days)

    extracted = fetch_courses_from_dhamma(location, date_current_course, end_date)  ## [4]

    # one day courses are possible in some centers !!!
    # extracted = [course for course in extracted if not course['raw_course_type'].startswith("1-Day")]

    for course in extracted:   ## [5]
        course.pop('sub_location', None)
        course.pop('center_non', None)
        if course['course_type_anchor'].endswith("OSC"):
            course['course_type_anchor'] = course['course_type_anchor'][:-3].strip()

    # FIXME use a .csv file instead and allow to change it in admin.

    df = pd.read_excel(db_path + 'course_type_map.xlsx')
    list_of_types = df.to_dict(orient='records')         ## [6]
    other_dict = get_field_from_db(db_central, center, "other_dict")
    periods_dhamma_org = [
        {
            "start_date": c.get("course_start_date"),
            "period_type": get_period_type(c.get("course_type_anchor"), c.get("course_type"), list_of_types, other_dict),
            "source": "dhamma.org",
            "course_type": c.get("course_type")
        }
        for c in extracted     ## [7]
    ]                         

    merged = periods_db_center + periods_dhamma_org            ## [8]
    mer_sort = sorted (merged,key=lambda x: x['start_date'])
    deduplicated = deduplicate(mer_sort)
    checked_draft_plan = check_plan(deduplicated, db_center) 

    return checked_draft_plan
```
[1] get the path to the center db, the gong db and the spreadsheet (see below)
[2] get the start date for the last course just before today = current course - or service
[3] get a dict. of all courses in the center db starting from the current course
[4] fetch extracted courses from dhamma.org
[5] Remove the last two fields: 'sub_location' and 'center_non'. Remove "OSC" suffix from 'raw_course_type' if present
[6] get the course_type mapping table from the spreadsheet
[7] and use it to map the course types from dhamma.org to center db
[8] merge the 2 course lists, sort the merge and deduplicate identical courses
 
