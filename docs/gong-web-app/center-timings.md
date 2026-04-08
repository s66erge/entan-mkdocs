# Center timings page

Will only be reachable for authenticated users and planner for the selected center.

```python
#| file: libs/timings.py 

import asyncio
import json
import os
import shutil
import pandas as pd
from tabulate import tabulate
from datetime import datetime
from zoneinfo import ZoneInfo
from fasthtml.common import *
import libs.utils as utils
import libs.cdash as cdash 
import libs.plancheck as plancheck
import libs.fetch as fetch
import libs.dbset as dbset
import libs.minio as minio
import libs.utilsJS as utilsJS

<<load-show-timetables>>
<<create-periods-table>>

```

### Planning page



```python
#| id: load-show-timetables

# @rt('/timings/load_center_periods')
def show_center_periods(session, centers):
    center = session[utils.Skey.CENTER]
    center_obj = centers[center]
    # load center_periods table from minio 
    table = plancheck.get_types_with_duration(center_obj)
    heads={"period_type": "Period type", "duration": "Duration", "time_start_first_day": "Tims start on first day", "time_end_last_day": "Time end on last day"}
    df = pd.DataFrame(table)
    html_content = df.to_html(index=False)
    return Div(
        H2("Center periods"),
        Div("",hx_swap_oob="true",id="planning-periods"),
        Div(Safe(html_content)
        ),
    )


```

### Create colored html table of current plan

```python
#| id: create-periods-table


```
