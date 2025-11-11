# Gong Planning System - Design Document

## Overview
Web app to manage gong planning data for meditation centers. Exports planning as SQLite to Raspberry Pi devices.

## Architecture

### User Roles
- **Admin**: Manage users, centers, assignments
- **Planner**: Create/update Structure and Timing for assigned centers
- **Visitor**: View-only access to all centers and planning

### Data Sources
1. **API-sourced** (dhamma.org): Courses and period types
2. **Admin-managed**: Structure, Timing, GongSounds

### Core Models
- `User` - Authentication & roles
- `Center` - Meditation centers (links to dhamma.org via location_id)
- `CenterAssignment` - Planners ↔ Centers (many-to-many)
- `Course` - Synced from dhamma.org API (quarterly)
- `Structure` - Day sequences per course type (composite PK: course_type + day_sequence)
- `Timing` - Gong times per day type (composite PK: course_type + day_type + gong_time)
- `GongSound` - Per-center wav files with strike config
- `Device` - Raspberry Pi devices with api_token
- `CenterExport` - Export versioning & checksums

### SQLite Export Schema (for Pi)
```sql
CREATE TABLE period_types (period_type TEXT PRIMARY KEY, struct_table TEXT, tt_table TEXT);
CREATE TABLE coming_periods (start_date TEXT PRIMARY KEY, period_type TEXT);
CREATE TABLE structure (period_type TEXT, day_sequence INTEGER, day_type TEXT, PRIMARY KEY (period_type, day_sequence));
CREATE TABLE timings (period_type TEXT, day_type TEXT, gong_time TEXT, gong_sound INTEGER, automatic_gong INTEGER, gong_description TEXT, PRIMARY KEY (period_type, day_type, gong_time));
CREATE TABLE gong_sounds (gong_sound INTEGER PRIMARY KEY, wav_file TEXT, num_strikes INTEGER, delay_ms INTEGER);
```


### Data Flow
1. Quarterly job fetches courses from dhamma.org API → populates courses table
2. Planners create Structure & Timing entries
3. Admins upload GongSounds per center
4. Pi polls nightly (00:30-02:30 CET): GET /api/centers/:id/export.sqlite?device_token=xxx
5. Server builds SQLite from courses + structures + timings + gong_sounds
6. Returns 304 if unchanged, else 200 + SQLite file

### API Integration
**Endpoint**: https://www.dhamma.org/en-US/courses/do_search Params: current_state=OldStudents, regions[]=location_XXXX, daterange=YYYY-MM-DD+-+YYYY-MM-DD, page=N Captures: course_type, course_type_anchor, course_start_date, course_end_date

## Next Steps
1. Run migrations
2. Create sync job for dhamma.org API
3. Create export service (SQLite builder)
4. Create API controller for Pi polling
5. Build admin UI (users, centers, assignments)
6. Build planner UI (structure, timing editor)
7. Build visitor UI (read-only calendar view)

## File Locations
- Models: app/models/*.rb
- Migrations: db/migrate/*.rb
- See chat history for complete code
- 
