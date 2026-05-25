This plan can only be saved if there are no red cell in the 'Check' field column.
You can modify it by deleting a line (Delete link in Action field), adding a new line (input form at bottom of table) or adding/changing period types in the center timetables where you can see complete periods information for this center (top 'timetables' buttons). The plan is completely recalculated after any modification and when you use the top button 'Load saved plan'.

##### Field information:
- **Start date**: will be sent to the center gong when plan and timetables are saved.
- **End date**: used to check the inegrity of the plan. Will NOT be sent to the center gong.
- **Period type**: period type names for the gong. See center configuration for the dhamma.org correspondance. 
- **Source**: either 'dhamma.org' or the center gong plan (*center name*.ok.db) or BOTH when it is the same period type and starting date. In this last case, then the 'End date' is the one from dhamma.org.
- **Check**: result of automatic plan check: see table below.
- **Info given by center in dhamma.org**: used to disambiguate dhamm.org period types: see the center configuration.
- **No_gong**: indicates the name of a period enclosed within the current period and ignored for the gong purpose: see the center configuration.

| Color | Check text | Explanation | Todo |
| -------- | -------- | --------- | -----|
| no |  | OK for the gong planning | nothing |
| no | OK Time overlap | time overlap on same day from a variable period | nothing |
| <span style="background-color:darkorange">orange</span> | CHECK Time overlap | time operlap on same day with another non variable period | check for conflict |
| <span style="background-color:darkorange">orange</span> | CHECK Overlap of X days,  | days operlap from a variable to a fixed period, likely combined with a gap(s) after the next period because the next period is inside the current period in dhamma.org |  decide if it is needed to use this period instead of the default period fill the following gap(s) |
| <span style="background-color:darkorange">orange</span> | CHECK GAP X days | A gap in the plan will be filled with the 'default period' | should be OK, just check |
| <span style="background-color:red">--red--</span> | NoType | no type in timetables for this period type | either delete/insert other period type or create one in timetables|
| <span style="background-color:red">--red--</span> | Same starting time | In the gong plan, 2 periods cannot have the same starting time | modify this and/or next period to suppress the identical starting time |
| <span style="background-color:red">--red--</span> | Overlap of X days | days overlap from a fixed to a fixed period | modify this and/or next period to suppress the overlap |
| <span style="background-color:red">--red--</span> | Missing time info | error in timetables for this period | correct timetable error |
<hr style="border: none; height: 4px; background-color: #3490dc;">