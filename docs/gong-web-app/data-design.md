# Database design

### Gong databases

One gong database is used to store the gong planning data for each center. Each gong database name is referenced in the CENTERS table in the Admin database below.
All gong databases have the same structure detailed here below, but their content will vary from center to center.

### ER diagrams

```mermaid
erDiagram

    COMING_PERIODS { 
        string start_date PK "ISO date string"
        string period_type FK 
   }

    COMING_PERIODS ||--|| PERIODS_STRUCT : "has this structure table"
    PERIODS_STRUCT {
        string period_type PK, FK
        int day_sequence PK "sequence of day: 0, 1, 2, ..."
        string day_type FK "'day 0', 'course day', 'last day'"
        }

    PERIODS_STRUCT  }o--o{ TIMETABLES : "day type has these timings"
    TIMETABLES {
        string period_type PK, FK
        string day_type PK,FK
        string gong_time PK "ISO time string"
        int gong_sound FK "gong sound to play"
        int automatic_gong "gong is automatic or manual (e.g.: depends on the kitchen)"
        string targets "list of Rasperry Pi(s) on this center that will ring this gong"
        string comment
    }

    TIMETABLES ||--|| GONGS : "gong sound is defined in this table"
    GONGS {
        int gong_sound PK
        int repeat
        float interval "in seconds"
        float length "in seconds"
        string comment
    }

    TIMETABLES ||--|| TARGETS : "gong targets are defined in this table"
    TARGETS {
        int id PK
        string shortname "short name of the target"
        string longname "long name of the target"
    }
```

### Web app database

The database is used to manage users, centers, and planners in the gong web app. It has the following entities:

ROLES:
- admin for modifying USERS / CENTERS / PLANNERS, and also gong planning 
- user for gong planning only

USERS:
- authenticated by sending a "magic link" to their email address : see "authenticate.md"

CENTERS:
- with the gong database name for this center

PLANNERS:
- indicates which user(s) can modify the gong planning of which center 

### ER diagrams

```mermaid
erDiagram

    ROLES { 
        string role_name PK
        text description
    }

    USERS  }o--|| ROLES : "has role"
    USERS {
        string email PK
        string name
        string role_name FK
        string last_login "ISO date-time string"
        string magic_link_token
        timestamp magic_link_expiry
        boolean is_active
        string timezone "from browser, e.g. 'Europe/Paris'"
    }

    CENTERS {
        string center_name PK
        string pi_db_date "ISO date string of last planning saved to the center"
        string status "current state machine status"
        string created_by "user who created the current planning"
        string status_start "ISO datetime for state machine current status"
        string center_save_date "ISO date for saving the current planning"
        string save_db_filename "name of file with planning to send to the center"
    }

    USERS ||--o{ PLANNERS : "is a"
    PLANNERS }o--|| CENTERS : for
    PLANNERS {
        string user_email PK, FK
        string center_name PK, FK
    }
```
