# Database design

### Gong databases

One gong database is used to store the gong planning data for each center. Each gong database name is referenced in the CENTERS table in the Admin database below.
All gong databases have the same structure detailed here below, but their content will vary from center to center.

As of today, this app is managing the gong planning for:

- Dhamma Mahi (mahi.db)
- Dhamma Pajjota (pajjota.db)


TODO describe the entities

```mermaid
erDiagram

    COMING_PERIODS  }o--|| PERIOD_TYPES : "is"
    COMING_PERIODS { 
        date start_date PK
        string period_type FK 
   }

    PERIOD_TYPES { 
        string period_type PK "e.g.: '10 days', 'Service','Trust WE' ..."
        string struct_table "name of the STRUCTURE table"
        string tt_table "name of the TIMINGS table"
    }

    PERIOD_TYPES ||--|| STRUCTURE : "has this structure table"
    STRUCTURE {
        int day_sequence PK "sequence of day: 0, 1, 2, ..."
        string day_type FK "'day 0', 'course day', 'last day'"
        }

    PERIOD_TYPES ||--|| TIMINGS : "has timings in this table"
    STRUCTURE  }o--o{ TIMINGS : "day type has these timings"
    TIMINGS {
        string day_type FK
        time gong_time
        int gong_sound
        boolean automatic_gong
        string gong_description
    }
```

### Admin database

The admin database is used to manage users, centers, and planners for gong planning. It has the following entities:

ROLES:
- admin for modifying USERS / CENTERS / PLANNERS, and also gong planning 
- user for gong planning only

USERS:
- authenticated by sending a "magic link" to their email address : see "authenticate.md"

CENTERS:
- with the gong database name for this center

PLANNERS:
- indicates which user(s) can modify the gong planning of which center 

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
        string magic_link_token
        timestamp magic_link_expiry
        boolean is_active
    }

    CENTERS {
        string center_name PK
        string gong_db_name
    }

    USERS ||--o{ PLANNERS : creates
    PLANNERS }o--|| CENTERS : for
    PLANNERS {
        string user_email PK, FK
        string center_name PK, FK
    }
```
