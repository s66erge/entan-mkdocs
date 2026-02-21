# ~/~ begin <<docs/gong-web-app/admin-show.md#libs/admin.py>>[init]
from fasthtml.common import *
from libs.utils import *

# ~/~ begin <<docs/gong-web-app/admin-show.md#show-users>>[init]

def show_users_table(users):
    User = users.dataclass()
    return Main(
        Table(
            Thead(
                Tr(Th("Email"), Th("Name"), Th("Role"), Th("Active"), Th("Action"))
            ),
            Tbody(
                *[Tr(
                    Td(u.email), 
                    Td(u.name or ""), 
                    Td(u.role_name), 
                    Td("Yes" if u.is_active else "No"),
                    Td(A("Delete", hx_post=f"/delete_user/{u.email}", hx_target="#users-feedback", hx_confirm="Are you sure you want to delete this user?"))
                ) for u in sorted(users(), key=lambda x: x.name)]
            )
        )
    )

def show_users_form(roles):
    Role = roles.dataclass()
    role_names = [r.role_name for r in roles()]
    return Main(
        Div(
            Form(
                Input(type="email", placeholder="User Email", name="new_user_email", required=True),
                Input(type="text", placeholder="User full name", name="name", required=True),                
                Select( 
                    Option("Select Role", value="", selected=True, disabled=True),
                    *[Option(role, value=role) for role in role_names],
                        name="role_name", required=True),
                Button("Add User", type="submit"), hx_post="/add_user",hx_target="#users-feedback"
            )
        )    
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-show.md#show-centers>>[init]

def show_centers_table(centers):
    Center = centers.dataclass()
    return Main(
        Table(
            Thead(
                Tr(Th("Name"), Th("timezone"), Th("Gong DB Name"), Th("status"), Th("current user"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(c.center_name),
                    Td(c.timezone),
                    Td(c.gong_db_name),
                    Td(c.status),
                    Td(c.current_user), 
                    Td(A("Delete", hx_post=f"/delete_center/{c.center_name}", hx_target="#centers-feedback", hx_confirm="Are you sure you want to delete this center?"))
                ) for c in sorted(centers(), key=lambda x: x.center_name)]
            )
        )
    )

def show_centers_form(centers):
    Center = centers.dataclass()
    center_dbs = sorted(c.gong_db_name for c in centers())
    return Main(
        Div(
            Form(
                Input(type="text", placeholder="Center Name", name="new_center_name", required=True),
                Input(type="text", placeholder="tz timezone (see: en.wikipedia.org/wiki/List_of_tz_database_time_zones)", name="new_timezone", required=True),
                Input(type="text", placeholder="Gong DB Name (without .db)", name="new_gong_db_name", required=True),
                Input(type="text", placeholder="Center location number (see: dhamma.org)", name="new_center_location", required=True),
                Select(
                    Option("Center planning to copy", value="", selected=True, disabled=True),
                    *[Option(cdb, value=cdb) for cdb in center_dbs],
                    name="db_template", required=True
                ),
                Button("Add Center", type="submit"), hx_post="/add_center",hx_target="#centers-feedback"
            )
        )
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-show.md#show-planners>>[init]

def show_planners_table(planners):
    Planner = planners.dataclass()
    return Main(
        Table(
            Thead(
                Tr(Th("User Email"), Th("Center Name"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(p.user_email), 
                    Td(p.center_name), 
                    Td(A("Delete", hx_post=f"/delete_planner/{p.user_email}/{p.center_name}", hx_target="#planners-feedback", hx_confirm='Are you sure you want to delete this planner association?'))
                ) for p in sorted(planners(), key=lambda x: x.center_name)]
            )
        )
    )

def show_planners_form(users, centers):
    Center = centers.dataclass()
    User = users.dataclass()
    sorted_centers = sorted(centers(), key=lambda x: x.center_name)
    sorted_users = sorted(users(), key=lambda x: x.name)
    return Main(
        Div(
            Form(
                Select(
                    Option("Select User", value="", selected=True, disabled=True),
                    *[Option(u.email, value=u.email) for u in sorted_users],
                    name="new_planner_user_email", required=True
                ),
                Select(
                    Option("Select Center", value="", selected=True, disabled=True),
                    *[Option(c.center_name, value=c.center_name) for c in sorted_centers],
                    name="new_planner_center_name", required=True
                ),
                Button("Add Planner", type="submit"), hx_post="/add_planner", hx_target="#planners-feedback"
            )
        )
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-show.md#admin-page>>[init]

# @rt('/admin_page')
def show_page(request, db):
    params = dict(request.query_params)
    users = db.t.users
    roles = db.t.roles
    centers = db.t.centers
    planners = db.t.planners
    return Main(
        Nav(
            Ul(
                Li(A("Dashboard", href="/dashboard")),
                Li(A("Contact", href="/unfinished")),
                Li(A("About", href="/unfinished")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(display_markdown("admin-t")),

        H2("Users"),
        Div(feedback_to_user(params), id="users-feedback"),
        Div(show_users_table(users), id="users-table"),
        H4("Add New User"),
        Div(show_users_form(roles), id="users-form"),

        H2("Centers"),
        Div(feedback_to_user(params), id="centers-feedback"),
        Div(show_centers_table(centers), id="centers-table"),
        H4("Add New Center"),
        Div(show_centers_form(centers), id="centers-form"),

        H2("Planners"),
        Div(feedback_to_user(params), id="planners-feedback"),
        Div(show_planners_table(planners), id="planners-table"),
        H4("Add New Planner"),
        Div(show_planners_form(users, centers), id="planners-form"),

        cls="container",
    )
# ~/~ end
# ~/~ end
