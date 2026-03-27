# ~/~ begin <<docs/gong-web-app/fetch-courses.md#libs/fetch.py>>[init]

import aiohttp
import json
import re
import asyncio
from tabulate import tabulate
from datetime import date
from fasthtml.common import *
import libs.plancheck as plancheck
import libs.utils as utils

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

def get_period_type(dhamma_type, course_type: str, dhamma_types, replacement):
    replace_dhamma = [r for r in replacement if r["raw_course_type"] == dhamma_type]
    if replace_dhamma:
        replace_all = [r for r in replace_dhamma if r["course_description"] == "@ALL@"]
        if replace_all:
            return replace_all[0]["period_type"]
        cleaned_type = re.sub(r'[^a-zA-Z0-9]', '', course_type).upper()
        replace_cleaned = [r for r in replace_dhamma if r["course_description"] in cleaned_type]
        if replace_cleaned:
            return replace_cleaned[0]["period_type"]    
    match_dhamma = [r for r in dhamma_types if r["raw_course_type"] == dhamma_type]
    if  match_dhamma:
        return match_dhamma[0]['period_type']
    return dhamma_type
# ~/~ end
# ~/~ begin <<docs/gong-web-app/fetch-courses.md#deduplicate>>[init]
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

# ~/~ end
# ~/~ begin <<docs/gong-web-app/fetch-courses.md#fetch-courses>>[init]

def get_dhamma_courses_types(extracted, center_obj, dhamma_types, replacement):
    for course in extracted:   ## [5]
        if course['course_type_anchor'].endswith("OSC"):
            course['course_type_anchor'] = course['course_type_anchor'][:-3].strip()

    periods_dhamma_org = [
        {
            "start_date": c.get("course_start_date"),
            "end_date": c.get("course_end_date"),
            "period_type": get_period_type(c.get("course_type_anchor"), c.get("course_type"), dhamma_types, replacement),
            "source": "dhamma.org",
            "course_type": c.get("course_type")
        }
        for c in extracted     ## [7]
    ]
    return periods_dhamma_org

def check_within(deletion_check, this_row, other_row):
    if other_row.get("period_type", "") != deletion_check:
        return False
    this_start = date.fromisoformat(this_row.get("start_date"))
    other_start = date.fromisoformat(other_row.get("start_date"))
    other_end = date.fromisoformat(other_row.get("end_date"))
    if this_start >= other_start and this_start < other_end:
        return True
    return False

def clean_dhamma_courses(periods_dhamma_org, dhamma_types, inside):
    cleaned = []
    default_type = next((x for x in dhamma_types if x.get("tags") == "D"), {}).get('period_type',"")  # Default type
    delete_list = [d for d in inside if d["action"] == "delete"]
    for i, row in enumerate(periods_dhamma_org):
        row_bef = cleaned[-1] if len(cleaned) > 0 else {}
        row_aft = periods_dhamma_org[i+1] if i < len(periods_dhamma_org) - 1 else {}
        to_delete = [d for d in delete_list if d["period_type"] == row["period_type"]]
        deletion_check = to_delete[0]["container"] if to_delete else "@TOKEEP@"
        if row["period_type"] == default_type or deletion_check == "@ALL@":
            continue
        elif check_within(deletion_check, row, row_bef) or check_within(deletion_check, row, row_aft):
            continue
        else:
            cleaned.append(row)
    return cleaned

async def fetch_dhamma_courses(centers, center, num_months, num_days):
    center_obj = centers[center]
    dhamma_types = utils.dicts_from_excel_in_db("all_centers", "dhamma_course")
    #print(tabulate(dhamma_types, headers="keys"))
    replacement = utils.dicts_from_excel_in_db(center_obj,"replacement")
    inside = utils.dicts_from_excel_in_db(center_obj,"inside")
    #print(tabulate(replacement, headers="keys"))
    # dhamma_location = f"location_{center_obj.location}"
    params = utils.params_from_excel_in_db(center_obj)
    dhamma_location = f"location_{params[utils.Pkey.LOCATION]}"

    periods_db_center, date_current_course = plancheck.coming_center_courses(center_obj)  ## [1-3]

    end_date = utils.add_months_days(date_current_course, num_months, num_days)

    extracted = await fetch_courses_from_dhamma(dhamma_location, date_current_course, end_date)  ## [4]
    #print(tabulate(extracted, headers="keys"))
    periods_dhamma_org = get_dhamma_courses_types(extracted, center_obj, dhamma_types, replacement)  ## [5]
    #print(tabulate(periods_dhamma_org, headers="keys"))
    cleaned_dhamma_org = clean_dhamma_courses(periods_dhamma_org, dhamma_types, inside)

    merged = periods_db_center + cleaned_dhamma_org
    # Sort by end_date descending first then RE_SORT EVERYTHING by start_date ascending
    # this keeps the first sorting order ok for identical start_dates
    mer_sort = sorted(sorted(merged, key=lambda x: x['end_date'], reverse=True),
                      key=lambda x: x['start_date'])
    deduplicated = deduplicate(mer_sort)

    return deduplicated
# ~/~ end
# ~/~ end
