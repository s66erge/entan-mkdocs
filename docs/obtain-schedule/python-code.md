# python program

Mahi location = 'location_1396'

Pajjota location = 'location_1370'

```python
import requests
from tabulate import tabulate

def fetch_dhamma_courses():
    url = "https://www.dhamma.org/en-US/courses/do_search"
    headers = {"User-Agent": "entan-mkdocs-fetcher/1.0"}
    all_courses = []
    
    # Initial page
    page = 1

    while True:
        data = {
            "current_state": "OldStudents",
            "regions[]": "location_1370",
            "daterange": "2025-12-10 - 2026-12-31",
            "page": str(page),
        }
        
        print(f"Fetching Dhamma courses - Page {page}...")
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

    # Remove the last two fields: 'sub_location' and 'center_non'
    for course in extracted:
        course.pop('sub_location', None)
        course.pop('center_non', None)
        # Remove "OSC" suffix from 'raw_course_type' and 'course_type_anchor' if present
        # if course['raw_course_type'].endswith("OSC"):
        #      course['raw_course_type'] = course['raw_course_type'][:-3].strip()
        if course['course_type_anchor'].endswith("OSC"):
            course['course_type_anchor'] = course['course_type_anchor'][:-3].strip()

    print(tabulate(extracted, headers="keys", tablefmt="grid"))

    return extracted

# Example usage:
if __name__ == "__main__":
    fetch_dhamma_courses()
```