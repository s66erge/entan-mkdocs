The course description entered by the center in dhamma.org is used to disambiguate when:
- the dhamma.org period `raw_course_type` is unspecified with 'Other'
- there is more than one gong period type for the dhamma.org period. Example: different gongs for 'center maintenance' and 'course preparation', both named 'ServicePeriod' in dhamma.org

Then the content of the dhamma.org course description is transformed:
1. stripped of all non alphanumeric characters: space, dash ...
2. then all alpha characters are moved to uppercase
And if the table `course_description` is contained in this transformed string, the table `period_type` is the retained gong period.