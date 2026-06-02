The program in the center minicomputer recognizes 3 type of periods:

- **fixed length** with each day having a specific gong timetable, as examples:
    + 10 day course with:
      - 'day 0' for the first day
      - 'course day' for days 1, 2, 3, 5, 6, 7, 8 and 9
      - 'vipassana day' for day 4
      - 'metta day' for day 10
      - 'last day' for day 11
    + Trust WE with:
      - 'com meeting' for the first day, which if often the same calendar day as the 'last day' of a 10 day course
      - 'trust meeting' for the second and last day  
- **variable length** periods have only one type of day 'repeating day' and its timetable is repeated until the start of the next period. As examples: 'service', 'course preparation', 'maintenance' ...
  + the **default period** is one of the variable periods is (often called 'IN BETWEEN'). Ita timetable is used:
    -  whenever there is a full-day gap in the gong planning
    -  between the last gong of the last day of a period and 1 a.m. on the next day (if there is any gong in the default period for this interval)

The gong program sent from this app to the center minicomputer is just the list of days with their starting period. The scheduling is:

- there can be only one period starting on any day
- a fixed period runs uninterrupted until the last gong of the last day
- a variable period runs until the start of the next period
- if there is any overlap between the end of a fixed period and the start of a variable period, the fixed period is first completed before using the variable period gong timetable
- gaps are filled with the default period as indicated above

The common worldwide schedule for all Vipassana centers is dhamma.org. But periods in dhamma.org can overlap, have gaps or be included inside another period, as an example: a one-day course inside a service period.
This app:
- gets the current dhamma.org planning
- identified from the center-specific configuration which gong planning period corresponds to a dhamma.org period
- merges the result with the current center gong planning, discards duplicates and uses the center configuration to make some center specific automatic adjustments  
- identifies and flags issues with the gong planning constraints above
- gives tools to the gong planner to adjust the gong planning and timetables until the gong plan/timetables are valid: they respect all constraints
- sends then the valid gong plan/timetables to the corresponding center at 1 a.m. local center time.

The task of the gong planner is to review the flagged issues and resolves them using the planning and timetables modification tools.
