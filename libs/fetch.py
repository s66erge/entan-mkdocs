# ~/~ begin <<docs/gong-web-app/fetch-courses.md#libs/fetch.py>>[init]
from pathlib import Path
# import pandas as pd  # moved to "myFasthtml.py"
# import aiohttp  # moved to "myFasthtml.py"
import json
import asyncio
from datetime import date
from myFasthtml import *
from libs.utils import add_months_days
from libs.dbset import get_db_path, get_central_db

# CONTINOW split this long file

# ~/~ begin <<docs/gong-web-app/fetch-courses.md#fetch-api>>[init]

async def fetch_courses_from_dhamma(location, date_start, date_end):
    url = "https://www.dhamma.org/en-US/courses/do_search"
    headers = {"User-Agent": "entan-mkdocs-fetcher/1.0"}
    all_courses = []

    page = 1

    async with aiohttp.ClientSession(headers=headers) as session:
        while True:
            data = {
                "current_state": "OldStudents",
                "regions[]": location,
                "daterange": f"{date_start} - {date_end}",
                "page": str(page),
            }

            print(f"Fetching courses Dhamma {location} - Page {page}...")
            try:
                async with session.post(url, data=data, timeout=15) as resp:
                    resp.raise_for_status()
                    payload = await resp.json()
            except aiohttp.ClientError as e:
                print("Request error:", e)
                return []
            except asyncio.TimeoutError as e:
                print("Request timeout:", e)
                return []
            except ValueError as e:
                # JSON decode error
                print("Invalid JSON:", e)
                return []

            courses = payload.get("courses", [])
            all_courses.extend(courses)

            total_pages = payload.get("pages", 0)
            if page >= total_pages:
                break

            page += 1

    extracted = [
        {
            "course_start_date": c.get("course_start_date"),
            "course_end_date": c.get("course_end_date"),
            "raw_course_type": c.get("raw_course_type"),
            "course_type_anchor": c.get("course_type_anchor"),
            "course_type": c.get("course_type")
        }
        for c in all_courses
        if c.get("location", {}).get("center_noncenter") != "noncenter"
    ]
    return extracted
# ~/~ end
# ~/~ begin <<docs/gong-web-app/fetch-courses.md#period-type>>[init]

def get_period_type(anchor, course_type: str, list_of_types, other_dict):
    replacements = other_dict.get("replacements")
    if replacements.get(anchor):
        course_type_dict = replacements[anchor]
        if course_type_dict.get("@ALL@"):
            return course_type_dict.get("@ALL@")
        cleaned_course_type_0 = ''.join(course_type.upper().split())
        cleaned_course_type = ''.join(cleaned_course_type_0.split('-'))
        for key, value in course_type_dict.items():
            if key in cleaned_course_type:
                return value
    for item in list_of_types:
        if  anchor == item.get('raw_course_type'):
            return item.get('period_type')
    return anchor
# ~/~ end
# ~/~ begin <<docs/gong-web-app/fetch-courses.md#deduplicate>>[init]
def get_list_of_types():
    db_path = get_db_path()
    df = pd.read_csv(db_path + 'course_type_map.csv')
    return df.to_dict(orient='records')

def get_types_with_duration(center_obj):
    list_of_types = get_list_of_types()
    selected_db = center_obj.gong_db_name
    db_center = database(get_db_path() + selected_db)
    for item in list_of_types:
        vt = item.get("period_type")
        days = [row.get("day") for row in list(db_center.t.periods_struct())
                if row.get("period_type") == vt and row.get("day") is not None]
        if item["tags"] == "F":
            item["duration"] = max(days) + 1
        else:
            item["duration"] = 0
        day_0_type = next((row.get("day_type") for row in list(db_center.t.periods_struct())
                 if row.get("period_type") == vt and row.get("day") == 0), None)
        times_day_0 = [row.get("time") for row in list(db_center.t.timetables())
                 if row.get("period_type") == vt and row.get("day_type") == day_0_type] 
        item["time_start_first_day"] = min(times_day_0)
        last_day_type = next((row.get("day_type") for row in list(db_center.t.periods_struct())
                 if row.get("period_type") == vt and row.get("day") == max(days)), None)
        times_last_day = [row.get("time") for row in list(db_center.t.timetables())
                 if row.get("period_type") == vt and row.get("day_type") == last_day_type] 
        item["time_end_last_day"] = max(times_last_day)
    return list_of_types

def deduplicate(merged):
    deduplicated = []
    i = 0
    while i < len(merged) -1:
        current = merged[i]
        if i + 1 < len(merged):
            next_item = merged[i + 1]
            if (current['start_date'] == next_item['start_date'] and 
                current['period_type'] == next_item['period_type'] and
                current['end_date'] == next_item['end_date'] and
                current['source'] != next_item['source']):
                # Mark as BOTH and skip the next one
                current['source'] = 'BOTH'
                deduplicated.append(current)
                i += 2  # skip next item
                continue
        deduplicated.append(current)
        i += 1
    return deduplicated

def check_plan(plan, selected_name, db):
    centers = db.t.centers
    types_with_duration = get_types_with_duration(centers[selected_name])    
    for idx, row in enumerate(plan):
        if idx == len(plan) - 1:
            row["check"] = "OK"
            continue
        next_start_date = plan[idx + 1].get("start_date")
        pt = row.get("period_type")
        try:
            e_this = date.fromisoformat(row.get("end_date"))
            s_next = date.fromisoformat(next_start_date) 
            delta_days = (s_next - e_this).days 
        except Exception:
            row["check"] = "InvalidDate"
        else:
            if row.get("start_date") == next_start_date and pt == plan[idx + 1].get("period_type"):
                row["check"] = "Duplicated periods"
            elif not pt in [t.get("period_type") for t in types_with_duration]:
                row["check"] = "NoType"
            elif delta_days < 0:
                row["check"] = f"Overlap of {- delta_days} day(s)"
            elif delta_days == 0:
                this_end_time = next((t.get("time_end_last_day") for t in types_with_duration
                                    if t.get("period_type") == pt), None)
                next_pt = plan[idx + 1].get("period_type")
                next_start_time = next((t.get("time_start_first_day") for t in types_with_duration
                                        if t.get("period_type") == next_pt), None)
                if this_end_time > next_start_time:
                    row["check"] = "CHECK Time overlap"
                else:
                    row["check"] = "OK same day"
            elif delta_days > 1:
                row["check"] = f"OK default {delta_days} days"
            else:
                row["check"] = "OK"
    return plan
# ~/~ end
# ~/~ begin <<docs/gong-web-app/fetch-courses.md#fetch-courses>>[init]

def add_end_dates(plan, center_obj):
    types_with_duration = get_types_with_duration(center_obj)
    for i in range(len(plan)):
        if 'end_date' not in plan[i] or plan[i]['end_date'] is None:
            this_type = list(filter(lambda x: x.get("period_type") == plan[i]['period_type'], types_with_duration))[0]
            if this_type["tags"] != "F":
                if i < len(plan) - 1:
                    next_start = plan[i+1].get('start_date')
                    plan[i]['end_date'] = add_months_days(next_start, 0, -1)
                else:
                    plan[i]['end_date'] = add_months_days(plan[i]['start_date'], 0, 1)
            else:
                plan[i]['end_date'] = add_months_days(plan[i]['start_date'], 0, this_type.get("duration") -1)
    return plan

def coming_center_courses(center_obj):
    #center = center_obj.center_name
    selected_db = center_obj.gong_db_name
    db_center = database(get_db_path() + selected_db)

    periods = db_center.t.coming_periods
    Period = periods.dataclass()
    count_past = sum(1 for item in periods() if date.fromisoformat(item.start_date) < date.today())
    date_current_course = periods()[count_past-1].start_date  ## [2]

    periods_db_center_obj = periods()[count_past-1:]  ## [3]
    periods_db_center = [
        {
            'start_date': p.start_date,
            'period_type': p.period_type,
            'source' : f"{center_obj.center_name.lower()}_db"

        }
        for p in periods_db_center_obj  ## [3]
    ]
    sorted_periods = sorted(periods_db_center, key=lambda x: x['start_date'])
    sorted_periods_ends = add_end_dates(sorted_periods, center_obj)
    return sorted_periods_ends, date_current_course

def get_dhamma_courses_types(extracted, center_obj, list_of_types):
    for course in extracted:   ## [5]
        if course['course_type_anchor'].endswith("OSC"):
            course['course_type_anchor'] = course['course_type_anchor'][:-3].strip()

    other_dict = json.loads(center_obj.other_course)  ## [6.1]
    periods_dhamma_org = [
        {
            "start_date": c.get("course_start_date"),
            "end_date": c.get("course_end_date"),
            "period_type": get_period_type(c.get("course_type_anchor"), c.get("course_type"), list_of_types, other_dict),
            "source": "dhamma.org",
            "course_type": c.get("course_type")
        }
        for c in extracted     ## [7]
    ]
    return periods_dhamma_org, other_dict

def check_within(deletion_check, this_row, other_row):
    if other_row.get("period_type", "") != deletion_check:
        return False
    this_start = date.fromisoformat(this_row.get("start_date"))
    other_start = date.fromisoformat(other_row.get("start_date"))
    other_end = date.fromisoformat(other_row.get("end_date"))
    if this_start >= other_start and this_start < other_end:
        return True
    return False

def clean_dhamma_courses(periods_dhamma_org, list_of_types, other_dict):
    cleaned = []
    default_type = next((x for x in list_of_types if x.get("tags") == "D"), {}).get('period_type',"")  # Default type
    delete_list = other_dict.get("delete", {})
    for i, row in enumerate(periods_dhamma_org):
        row_bef = cleaned[-1] if len(cleaned) > 0 else {}
        row_aft = periods_dhamma_org[i+1] if i < len(periods_dhamma_org) - 1 else {}
        deletion_check = delete_list.get(row["period_type"], "@TOKEEP@")
        if row["period_type"] == default_type or deletion_check == "@ALL@":
            continue
        elif check_within(deletion_check, row, row_bef) or check_within(deletion_check, row, row_aft):
            continue
        else:
            cleaned.append(row)
    return cleaned

async def fetch_dhamma_courses(center, num_months, num_days):
    db_central = get_central_db()
    centers = db_central.t.centers
    Center = centers.dataclass()
    center_obj = centers[center]
    list_of_types = get_list_of_types()

    periods_db_center, date_current_course = coming_center_courses(center_obj)  ## [1-3]

    dhamma_location = f"location_{center_obj.location}"
    end_date = add_months_days(date_current_course, num_months, num_days)

    extracted = await fetch_courses_from_dhamma(dhamma_location, date_current_course, end_date)  ## [4]
    periods_dhamma_org, other_dict = get_dhamma_courses_types(extracted, center_obj, list_of_types)  ## [5]
    cleaned_dhamma_org = clean_dhamma_courses(periods_dhamma_org, list_of_types, other_dict)

    merged = periods_db_center + cleaned_dhamma_org
    # Sort by end_date descending first then RE_SORT EVERYTHING by start_date ascending
    # this keeps the first sorting order ok for identical start_dates
    mer_sort = sorted(sorted(merged, key=lambda x: x['end_date'], reverse=True),
                      key=lambda x: x['start_date'])
    deduplicated = deduplicate(mer_sort)

    return deduplicated
# ~/~ end
# ~/~ end
