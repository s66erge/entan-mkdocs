# Admin page

Will only be reachable for signed in admin users.

```{.python #admin-show-md}

<<show-users>>
<<show-centers>>
<<show-planners>>
<<admin-page>>
```

TODO document admin-show

```{.python #admin-page}

@rt('/admin_page')
@admin_required
def admin(session, request):
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
        Div(utils.display_markdown("admin-show")),
        feedb.feedback_to_user(params),

        H2("Users"),
        Div(feedb.feedback_to_user(params), id="users-feedback"),
        Div(show_users_table(), id="users-table"),
        H4("Add New User"),
        Div(show_users_form(), id="users-form"),

        H2("Centers"),
        Div(feedb.feedback_to_user(params), id="centers-feedback"),
        Div(show_centers_table(), id="centers-table"),
        H4("Add New Center"),
        Div(show_centers_form(), id="centers-form"),

        # show_planners(),
        H2("Planners"),
        Div(feedb.feedback_to_user(params), id="planners-feedback"),
        Div(show_planners_table(), id="planners-table"),
        H4("Add New Planner"),
        Div(show_planners_form(), id="planners-form"),

        cls="container",
    )
```



```{.python #show-users}

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
                    Td(A("Delete", hx_post=f"/delete_user/{u.email}", hx_target="#users-feedback", hx_confirm="Are you sure you want to delete this user?"))
                ) for u in sorted(users(), key=lambda x: x.name)]
            )
        )
    )


def show_users_form():
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

```{.python #show-centers}

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
                    Td(A("Delete", hx_post=f"/delete_center/{c.center_name}", hx_target="#centers-feedback", hx_confirm="Are you sure you want to delete this center?"))
                ) for c in sorted(centers(), key=lambda x: x.center_name)]
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

```{.python #show-planners}

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
                    Td(A("Delete", hx_post=f"/delete_planner/{p.user_email}/{p.center_name}", hx_target="#planners-feedback", hx_confirm='Are you sure you want to delete this planner association?'))
                ) for p in sorted(planners(), key=lambda x: x.center_name)]
            )
        )
    )

def show_planners_form():
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
