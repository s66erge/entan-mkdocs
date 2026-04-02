# Admin page

Will only be reachable for signed in admin users.

```python
#| file: libs/admin.py 

import asyncio
from fasthtml.common import *
import libs.utils as utils
import libs.states as states
import libs.minio as minio

<<show-users>>
<<show-centers>>
<<show-planners>>
<<admin-page>>
<<up-down-config>>
```
TODO document admin-show

```python
#| id: admin-page

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
```

```python
#| id: show-users
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
```

```python
#| id: show-centers

def show_centers_table(centers):
    return Main(
        Table(
            Thead(
                Tr(Th("Name"), Th("status"), Th("current user"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(c.center_name),
                    Td(c.status),
                    Td(c.created_by), 
                    Td(A("Delete", hx_post=f"/delete_center/{c.center_name}", hx_target="#centers-feedback",
                         hx_confirm="Are you ABSOLUTELY sure you want to delete this center?"))
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
                Select(
                    Option("Center planning and config to copy", value="", selected=True, disabled=True),
                    *[Option(c, value=c) for c in center_names],
                    name="center_template", required=True
                ),
                Button("Add Center", type="submit"), hx_post="/add_center",hx_target="#centers-feedback"
            )
        )
    )
```

```python
#| id: show-planners

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
```

```python
#| id: up-down-config

def upload_form(centers):
    sorted_centers = sorted(centers(), key=lambda x: x.center_name)
    return Form(hx_post="upload_config", hx_target="#config-feedback",
                hx_confirm="Are you ABSOLUTELY sure to change this center configuration?")(
            Select(
                Option("Select Center", value="", selected=True, disabled=True),
                Option("All Centers", value="all_centers"),
                *[Option(c.center_name, value=c.center_name) for c in sorted_centers],
                name="center_name", required=True
            ),
            Input(type="file", name="file"),
            Button("Upload", type="submit"),
        ),

def download_form(centers):
    sorted_centers = sorted(centers(), key=lambda x: x.center_name)
    return Form(hx_get="/download_config/", hx_target="#config-feedback")(
            Select(
                Option("Select Center", value="", selected=True, disabled=True),
                Option("All Centers", value="ALL"),
                *[Option(c.center_name, value=c.center_name) for c in sorted_centers],
                name="center_name", required=True
            ),
            Button("Download", type="submit", hx_swap="none"),
        ),

async def upload_config(file: UploadFile, center_name: str):
    if file.filename != f"{center_name}.xlsx":
        mess = {"error": "bad_config_filename"}
    elif center_name != "all_centers" and states.csms[center_name].configuration[0].id != "free":
        mess = {"error": "center_not_free"}
    else:
        try:
            filebuffer = await file.read()
            upload_dir = Path(utils.get_db_path())
            (upload_dir / file.filename).write_bytes(filebuffer)
            await asyncio.to_thread(minio.save_excel_minio, center_name)
            mess = {"success": "config_uploaded"}
        except Exception as e:
            return Redirect(f'/db_error?etext={e}')
    return Div(utils.feedback_to_user(mess))

async def download_config(session, request):
    try:
        params = dict(request.query_params)
        center_name = params.get("center_name")
        await asyncio.to_thread(minio.get_excel_minio, center_name)
        #minio.get_excel_minio(center_name)
        session[utils.Skey.CENTER] = center_name
        return Redirect("/download_it")
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')

```
