# dhamma.org courses API 

## Request

- POST request
**Request URL:** https://www.dhamma.org/en-US/courses/do_search
- current_state=OldStudents&regions[]=location_1370&daterange=2025-11-02 - 2026-11-02&page=1
- iterate over pages until reaching the ‘pages’ at the end of the Response

## Response

Summary with relevant fields
    
```json
{
    "courses": [
    {
        "id": 191183,
        "local_time": "2025-11-02T17:23:43.000+00:00",
        "course_start_date": "2026-02-25",
        "course_end_date": "2026-03-08",
        "enrollment_open_date": "2025-11-25",
        "localized_start_date": "Feb 25 2026",
        "localized_end_date": "Mar 08 2026",
        "raw_course_type": "10-Day",
        "course_type_number_nights": 11,
        "course_type_anchor": "10-Day",
        "course_type": "10 days",
        "location": {
        "id": 1370,
        "sub_domain": "pajjota",
        "dhamma_name": "Dhamma Pajjota",
        ...
        "sub_location": empty, # for Pajjota, else "Brussels" or "Ghent"
        "center_noncenter": "center", # "noncenter" if not Pajjota
        }
    }
    {other courses...}
    ],
    "page": 3,
    "pages": 7,
    "total_rows": 63,
    "formatted_total_rows": "63",
    "pages_truncated": false,
    "saved_search_uuid": "68f422a6-66cb-4a73-bc51-d4d43ef0a256",
    "saved_search_params": {
    "current_state": "OldStudents",
    "regions": [
        "location_1370"
    ]
    }
}
```