# Admin page

Will only be reachable for signed in admin users.

``` {.python #admin-show}

<<show-users>>
<<show-centers>>
<<show-planners>>
<<admin-page>>
```

TODO document admin-show

TODO show tables sorted by key

``` {.python #admin-page}

@rt('/admin_page')
def admin(session, request):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return Main(
            Nav(Li(A("Dashboard", href="/dashboard"))),
            Div(H1("Access Denied"),
                P("You do not have permission to access this page.")),
            cls="container")
    params = dict(request.query_params)
    return Main(
        Nav(
            Ul(
                Li(A("Dashboard", href="/dashboard")),
                Li(A("Contact", href="#")),
                Li(A("About", href="#")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(display_markdown("admin-show")),
        feedback_to_user(params),

        H2("Users"),
        Div(feedback_to_user(params), id="users-feedback"),
        Div(show_users_table(), id="users-table"),
        H4("Add New User"),
        Div(show_users_form(), id="users-form"),

        H2("Centers"),
        Div(feedback_to_user(params), id="centers-feedback"),
        Div(show_centers_table(), id="centers-table"),
        H4("Add New Center"),
        Div(show_centers_form(), id="centers-form"),

        # show_planners(),
        H2("Planners"),
        Div(feedback_to_user(params), id="planners-feedback"),
        Div(show_planners_table(), id="planners-table"),
        H4("Add New Planner"),
        Div(show_planners_form(), id="planners-form"),

        cls="container",
    )
```



``` {.python #show-users}

def show_users_table():
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
                    Td(A("Delete", hx_post=f"/delete_user/{u.email}", hx_target="#users-feedback", onclick="return confirm('Are you sure you want to delete this user?')"))
                ) for u in users()]
            )
        )
    )


def show_users_form():
    role_names = [r.role_name for r in roles()]
    return Main(
        Div(
            Form(
                Input(type="email", placeholder="User Email", name="new_user_email", required=True),
                Select( 
                    Option("Select Role", value="", selected=True, disabled=True),
                    *[Option(role, value=role) for role in role_names],
                        name="role_name", required=True),
                Button("Add User", type="submit"), hx_post="/add_user",hx_target="#users-feedback"
            )
        )    
    )
```

``` {.python #show-centers}

def show_centers_table():
    return Main(
        Table(
            Thead(
                Tr(Th("Center Name"), Th("Gong DB Name"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(c.center_name), 
                    Td(c.gong_db_name), 
                    Td(A("Delete", hx_post=f"/delete_center/{c.center_name}",
                        hx_target="#centers-feedback", onclick="return confirm('Are you sure you want to delete this center?')"))
                ) for c in centers()]
            )
        )
    )

def show_centers_form():
    return Main(
        Div(
            Form(
                Input(type="text", placeholder="Center Name", name="new_center_name", required=True),
                Input(type="text", placeholder="Gong DB Name (without .db)", name="new_gong_db_name", required=True),
                Small("The database file will be created as a copy of mahi.db"),
                Button("Add Center", type="submit"), hx_post="/add_center",hx_target="#centers-feedback"
            )
        )
    )
```

DONOW adapt to htmx calls

``` {.python #show-planners}

def show_planners_table():
    return Main(
        Table(
            Thead(
                Tr(Th("User Email"), Th("Center Name"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(p.user_email), 
                    Td(p.center_name), 
                    Td(A("Delete", href=f"/delete_planner/{p.user_email}/{p.center_name}",
                            onclick="return confirm('Are you sure you want to delete this planner association?')"))
                ) for p in planners()]
            )
        )
    )

def show_planners_form():
    return Main(
        Div(
            Form(
                Select(
                    Option("Select User", value="", selected=True, disabled=True),
                    *[Option(u.email, value=u.email) for u in users()],
                    name="new_planner_user_email", required=True
                ),
                Select(
                    Option("Select Center", value="", selected=True, disabled=True),
                    *[Option(c.center_name, value=c.center_name) for c in centers()],
                    name="new_planner_center_name", required=True
                ),
                Button("Add Planner", type="submit"),
                method="post", action="/add_planner"
            )
        )
    )
```
