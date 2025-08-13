# User pages

Will only be reachable for users who are signed in.

``` {.python #admin-show-md}

<<show-users>>
<<show-centers>>
<<show-planners>>
<<admin-page>>
```

TODO document admin-show

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

    # Handle success and error messages
    query_params = dict(request.query_params)
    message_div = None

    if 'success' in query_params:
        success_messages = {
            'user_added': 'User added successfully!',
            'center_added': 'Center added successfully!',
            'planner_added': 'Planner association added successfully!',
            'user_deleted': 'User deleted successfully!',
            'center_deleted': 'Center and associated database deleted successfully!',
            'planner_deleted': 'Planner association deleted successfully!'
        }
        message = success_messages.get(query_params['success'], 'Operation completed successfully!')
        message_div = Div(P(message), style="color: #d1f2d1; background: #0f5132; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #198754; font-weight: 500;")

    elif 'error' in query_params:
        error_messages = {
            'missing_fields': 'Please fill in all required fields.',
            'user_exists': 'User with this email already exists.',
            'center_exists': 'Center with this name already exists.',
            'planner_exists': 'This planner association already exists.',
            'user_not_found': 'User not found.',
            'center_not_found': 'Center not found.',
            'invalid_role': 'Invalid role selected.',
            'database_error': 'Database error occurred. Please try again.',
            'db_file_exists': 'Database file with this name already exists.',
            'template_not_found': 'Template database (mahi.db) not found.',
            'user_has_planners': f'Cannot delete user. User is still associated with centers: {query_params.get("centers", "")}. Please remove all planner associations first.',
            'center_has_planners': f'Cannot delete center. Center is still associated with users: {query_params.get("users", "")}. Please remove all planner associations first.',
            'last_planner_for_center': f'Cannot delete planner. This is the last planner for center "{query_params.get("center", "")}". Each center must have at least one planner.'
        }
        message = error_messages.get(query_params['error'], 'An error occurred.')
        message_div = Div(P(message), style="color: #f8d7da; background: #842029; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #dc3545; font-weight: 500;")

    return Main(
        Nav(
            Ul(
                Li(A("Dashboard", href="/dashboard")),
                Li(A("Contact", href="#")),
                Li(A("About", href="#")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(H1("Admin Dashboard"), P("Here you can manage users, centers, and planners.")),
        message_div,
        show_users(),
        show_centers(),
        show_planners(),
        cls="container",
    )
```

``` {.python #show-users}
def show_users():
    return Main( 
        Div(
        Table(
        H2("Users"),
            Thead(
                Tr(Th("Email"), Th("Name"), Th("Role"), Th("Active"), Th("Action"))
            ),
            Tbody(
                *[Tr(
                    Td(u.email), 
                    Td(u.name or ""), 
                    Td(u.role_name), 
                    Td("Yes" if u.is_active else "No"),
                    Td(A("Delete", href=f"/delete_user/{u.email}", 
                        onclick="return confirm('Are you sure you want to delete this user?')"))
                ) for u in users()]
            )
        )
    ),
    Div(
        H4("Add New User"),
        Form(
            Input(type="email", placeholder="User Email", name="new_user_email", required=True),
            Select( 
                Option("Select Role", value="", selected=True, disabled=True),
                Option("Admin", value="admin"),
                Option("User", value="user"),
                    name="role_name", required=True),
            Button("Add User", type="submit"),
            method="post",
            action="/add_user"
            )
        )    
    )
```

``` {.python #show-centers}
def show_centers():
    return Main(
        Div(
        H2("Centers"),
        Table(
            Thead(
                Tr(Th("Center Name"), Th("Gong DB Name"), Th("Actions"))
            ),
            Tbody(
                *[Tr(
                    Td(c.center_name), 
                    Td(c.gong_db_name), 
                    Td(A("Delete", href=f"/delete_center/{c.center_name}",
                        onclick="return confirm('Are you sure you want to delete this center?')"))
                    ) for c in centers()]
                )
            )
        ),
        Div(
            H4("Add New Center"),
            Form(
                Input(type="text", placeholder="Center Name", name="new_center_name", required=True),
                Input(type="text", placeholder="Gong DB Name (without .db)", name="new_gong_db_name", required=True),
                Small("The database file will be created as a copy of mahi.db"),
                Button("Add Center", type="submit"),
                method="post",
                action="/add_center"
            )
        )
    )
```

``` {.python #show-planners}
def show_planners():
    return Main(
        Div(
            H2("Planners"),
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
        ),
        Div(
            H4("Add New Planner"),
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
                method="post",
                action="/add_planner"
            )
        )
    )
```
