# ~/~ begin <<docs/gong-web-app-code/fetch-courses.md#libs/fetch.py>>[init]

from curl_cffi import requests
import re
import asyncio
from datetime import date
from fasthtml.common import *
import libs.plancheck as plancheck
import libs.utils as utils
import libs.minio as minio

# ~/~ begin <<docs/gong-web-app-code/fetch-courses.md#fetch-api>>[init]

def fetch_scrap(location, date_start, date_end):
    # Initialize a session that mimics a modern Chrome browser
    session = requests.Session(impersonate="chrome")
    all_courses = []
    page = 1
    while True:
        print(f"Scraping courses Dhamma {location} - Page {page}...")
        # curl_cffi uses the standard 'data' parameter for form-encoded POST requests
        response = session.post(
            "https://www.dhamma.org/en-US/courses/do_search",
            data={
                "current_state": "OldStudents",
                "regions[]": location,
                "daterange": f"{date_start} - {date_end}",
                "page": page,
            }
        )
        # Parse the JSON response
        payload = response.json()
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
        if c.get("location", {}).get("center_noncenter") != "noncenter" and \
            c.get("status", [{}])[0].get("status", "").upper() != "CANCELLED"
    ]   
    return extracted


# ~/~ end
# ~/~ begin <<docs/gong-web-app-code/fetch-courses.md#period-type>>[init]

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
# ~/~ begin <<docs/gong-web-app-code/fetch-courses.md#deduplicate>>[init]

def deduplicate(merged):
    deduplicated = []
    i = 0
    while i < len(merged):
        current = merged[i]
        if i + 1 < len(merged):
            next_item = merged[i + 1]
            if (current['start_date'] == next_item['start_date'] and 
                current['period_type'] == next_item['period_type'] and
                # current['end_date'] == next_item['end_date'] and
                current['source'] != next_item['source']):
                # Mark as BOTH and keep the "dhamma.org" one
                if current['source'] == "dhamma.org":
                    current['source'] = 'BOTH'
                    deduplicated.append(current)
                else:
                    next_item['source'] = 'BOTH'
                    deduplicated.append(next_item)
                i += 2  # skip next item
                continue
        deduplicated.append(current)
        i += 1
    return deduplicated

# ~/~ end
# ~/~ begin <<docs/gong-web-app-code/fetch-courses.md#fetch-courses>>[init]

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

def check_within(this_row, row_aft):
    this_start = date.fromisoformat(this_row.get("start_date"))
    other_start = date.fromisoformat(row_aft.get("start_date"))
    other_end = date.fromisoformat(row_aft.get("end_date"))
    if this_start >= other_start and this_start < other_end:
        return True
    return False

def clean_dhamma_courses(center, periods_dhamma_org, inside):
    cleaned = []
    delete_list = [d for d in inside if d["action"] == "delete"]
    insert1_list = [d for d in inside if d["action"] == "insert1"]
    for i, row in enumerate(periods_dhamma_org):
        if i == 0:
            cleaned.append(row)
            continue
        row_bef = periods_dhamma_org[i-1]

        row_delete_list = [d for d in delete_list if d["period_type"] == row["period_type"]]
        if row_delete_list:
            if row_delete_list[0]["container"] == "@ALL@":
                # row_bef["No_gong"] = row["period_type"]
                cleaned[-1]["No_gong"] = row["period_type"]
                continue
            elif [d for d in row_delete_list if d["container"] == row_bef["period_type"] \
                                            and check_within(row, row_bef)]:
                # row_bef["No_gong"] = row["period_type"]
                cleaned[-1]["No_gong"] = row["period_type"]
                continue
            else:
                cleaned.append(row)
                continue
        elif [d for d in insert1_list if d["container"] == row["period_type"]]:
            first_period_duration = [d for d in plancheck.get_types_with_duration(center) 
                                        if d["period_type"] == row["period_type"]][0]["duration"]
            end_first_period = utils.add_months_days(row["start_date"], 0, first_period_duration - 1)
            first_row = {
                "start_date": row["start_date"],
                "end_date": end_first_period,
                "period_type": insert1_list[0]["period_type"],
                "source": row["source"] + " + CONFIG."
                    if not row["source"].endswith("CONFIG.") else row["source"],
                "course_type": row["course_type"],
                "no_gong": row["no_gong"] if "no_gong" in row else None
            }
            cleaned.append(first_row)
            second_row = {
                "start_date": utils.add_months_days(end_first_period, 0, 1),
                "end_date": row["end_date"],
                "period_type": insert1_list[0]["after"],
                "source": row["source"] + " + CONFIG."
                    if not row["source"].endswith("CONFIG.") else row["source"],
                "course_type": row["course_type"],
                "no_gong": row["no_gong"] if "no_gong" in row else None
            }
            cleaned.append(second_row)
            continue
        else:
            cleaned.append(row)
    return cleaned

def fillgaps_dhamma_courses(periods_dhamma_org, inside):
    filled = []
    fillin_list = [d for d in inside if d["action"] == "fillin"]
    fillin_period = fillin_list[0]["period_type"] if fillin_list else None
    for i, row in enumerate(periods_dhamma_org):
        if i == 0:
            filled.append(row)
            continue
        row_bef = periods_dhamma_org[i-1]
        delta_days = utils.days_between_iso_dates(row_bef.get("end_date"), row.get("start_date"))
        if fillin_period and delta_days > 1:
            fillin_row = {
                "start_date": utils.add_months_days(row_bef["end_date"], 0, 1),
                "end_date": row["start_date"],
                "period_type": fillin_period,
                "source": "fill gap",
                "course_type": "",
                "no_gong": ""
            }
            filled.append(fillin_row)
        filled.append(row)
    return filled

def sort_clean(center,aplan, inside):
    # Sort by end_date descending first then RE_SORT EVERYTHING by start_date ascending
    # this keeps the first sorting order ok for identical start_dates
    sorted_plan = sorted(sorted(aplan, key=lambda x: x['end_date'], reverse=True),
                      key=lambda x: x['start_date'])
    dedup = deduplicate(sorted_plan)
    dedup_cleaned = clean_dhamma_courses(center, dedup, inside)
    cleaned_filled = fillgaps_dhamma_courses(dedup_cleaned, inside)
    return cleaned_filled

async def fetch_dhamma_courses(centers, center, num_months, num_days):
    center_obj = centers[center]
    # get the course_type mapping table from the spreadsheet
    dhamma_types = minio.dicts_from_excel("all_centers", "dhamma_course")
    replacement = minio.dicts_from_excel(center,"replacement")
    inside = minio.dicts_from_excel(center,"inside")
    params = minio.params_from_excel(center)
    dhamma_location = f"location_{params[utils.Pkey.LOCATION]}"

    # get the start date for the last course just before today = current course - or service
    periods_db_center, date_current_course = plancheck.coming_center_courses(center)

    end_date = utils.add_months_days(date_current_course, num_months, num_days)

    # fetch extracted courses from dhamma.org
    extracted = await asyncio.to_thread(fetch_scrap, dhamma_location, date_current_course, end_date)

    # get the course_type for each extracted course from the mapping and replacements tables
    periods_dhamma = get_dhamma_courses_types(extracted, center_obj, dhamma_types, replacement)

    # merge the 2 course lists, sort the merge and deduplicate identical courses
    merged = periods_db_center + periods_dhamma
    dedup_cleaned = sort_clean(center,merged, inside)
    return dedup_cleaned
# ~/~ end
# ~/~ end
