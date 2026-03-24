# ~/~ begin <<docs/gong-web-app/admin-show.md#libs/admin.py>>[init]

from fasthtml.common import *
import libs.utils as utils
import libs.plancheck as plancheck

# ~/~ begin <<docs/gong-web-app/admin-show.md#show-users>>[init]
def show_users_table(users):
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
                    Td(c.created_by), 
                    Td(A("Delete", hx_post=f"/delete_center/{c.center_name}", hx_target="#centers-feedback",
                         hx_confirm="Are you ABSOLUTELY sure you want to delete this center?"),
                       Span(style="display: inline-block; width: 20px;"),
                       A("Download config", hx_post=f"/download_center_config/{c.center_name}", hx_target="#centers-feedback")
                    )
                ) for c in sorted(centers(), key=lambda x: x.center_name)]
            )
        )
    )

def show_centers_form(centers):
    center_names = sorted(c.center_name for c in centers())
    return Main(
        Div(
            Form(
                Input(type="text", placeholder="Center Name", name="new_center_name", required=True),
                Input(type="text", placeholder="tz timezone (see: en.wikipedia.org/wiki/List_of_tz_database_time_zones)", name="new_timezone", required=True),
                Input(type="text", placeholder="Gong DB Name (without .db)", name="new_gong_db_name", required=True),
                Input(type="text", placeholder="Center location number (see: dhamma.org)", name="new_center_location", required=True),
                Select(
                    Option("Center planning and config to copy", value="", selected=True, disabled=True),
                    *[Option(cdb, value=cdb) for cdb in center_names],
                    name="db_template", required=True
                ),
                Button("Add Center", type="submit"), hx_post="/add_center",hx_target="#centers-feedback"
            )
        )
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-show.md#show-planners>>[init]

def show_planners_table(planners):
    return Main(
        Table(
            Thead(
                Tr(Th("User Email"), Th("Center Name"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(p.user_email), 
                    Td(p.center_name), 
                    Td(A("Delete", hx_post=f"/delete_planner/{p.user_email}/{p.center_name}", hx_target="#planners-feedback",
                         hx_confirm='Are you sure you want to delete this planner association?'))
                ) for p in sorted(planners(), key=lambda x: x.center_name)]
            )
        )
    )

def show_planners_form(users, centers):
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
def show_page(request, users, roles, centers, planners):
    params = dict(request.query_params)
    return Main(
        Nav(
            Ul(
                Li(A("Dashboard", href="/dashboard")),
                Li(A("Contact", href="/unfinished")),
                Li(A("About", href="/unfinished")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(utils.display_markdown("admin-t")),

        H2("Users"),
        Div(utils.feedback_to_user(params), id="users-feedback"),
        Div(show_users_table(users), id="users-table"),
        H4("Add New User"),
        Div(show_users_form(roles), id="users-form"),

        H2("Centers"),
        Div(utils.feedback_to_user(params), id="centers-feedback"),
        Div(show_centers_table(centers), id="centers-table"),
        H4("Add New Center"),
        Div(show_centers_form(centers), id="centers-form"),

        H2("Planners"),
        Div(utils.feedback_to_user(params), id="planners-feedback"),
        Div(show_planners_table(planners), id="planners-table"),
        H4("Add New Planner"),
        Div(show_planners_form(users, centers), id="planners-form"),

        H2("Center configuration"),
        Div(utils.feedback_to_user(params), id="config-feedback"),
        H4("Upload a new configuration excel file and copy it in database"),
        upload_form(centers),
        H4("Download a center configuration excel file from the database"),
        download_form(centers),
        cls="container",
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/admin-show.md#up-down-config>>[init]

def upload_form(centers):
    sorted_centers = sorted(centers(), key=lambda x: x.center_name)
    return Form(hx_post="upload_config", hx_target="#config-feedback",
                hx_confirm="Are you ABSOLUTELY sure to change this center configuration?")(
            Select(
                Option("Select Center", value="", selected=True, disabled=True),
                *[Option(c.center_name, value=c.center_name) for c in sorted_centers],
                name="center_name", required=True
            ),
            Input(type="file", name="file"),
            Button("Upload", type="submit"),
        ),

def download_form(centers):
    sorted_centers = sorted(centers(), key=lambda x: x.center_name)
    return Form(hx_get="/download_config", hx_target="#config-feedback")(
            Select(
                Option("Select Center", value="", selected=True, disabled=True),
                *[Option(c.center_name, value=c.center_name) for c in sorted_centers],
                name="center_name", required=True
            ),
            Button("Download", type="submit", hx_swap="none"),
        ),

async def upload_config(file: UploadFile, center_name: str, centers):
    if file.filename != f"{center_name}.xlsx":
        mess = {"error": "bad_config_filename"}
    else:
        try:
            filebuffer = await file.read()
            upload_dir = Path(utils.get_db_path())
            (upload_dir / file.filename).write_bytes(filebuffer)
            plancheck.load_excel_in_db(center_name, centers)
            mess = {"success": "config_uploaded"}
        except Exception as e:
            return Redirect(f'/db_error?etext={e}')
    return Div(utils.feedback_to_user(mess))

async def download_config(session, request, centers):
    try:
        params = dict(request.query_params)
        center_name = params.get("center_name")
        center_obj = centers[center_name]
        plancheck.get_excel_from_db(center_obj)
        filename = center_name + ".xlsx"
        session["filename"] = filename
        return Redirect("/download_it")
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')





# ~/~ end
# ~/~ end
