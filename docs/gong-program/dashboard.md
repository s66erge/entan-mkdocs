# User pages

Will only be reachable for users who are signed in.

``` {.python #start-admin-md}

<<dashboard>>
<<admin-page>>
<<delete-routes>>
<<insert-routes>>
```

TODO separate admin from dashboard

TODO do not delete the last planner of a center

``` {.python #dashboard}

@rt('/dashboard')
def get(session): 
    sessemail = session['auth']
    u = users[sessemail]
    centers = planners("user_email = ?", (u.email,))
    center_names = ", ".join(c.center_name for c in centers)
    return Main(
        Nav(
            Ul(
                Li(A("Admin", href="/admin")) if u.role_name == "admin" else None ,
                Li(A("Contact", href="#")),
                Li(A("About", href="#")),
            ), 
            Button("Logout", hx_post="/logout"),
        ),
        Div(H1("Dashboard"), P(f"You are logged in as '{u.email}' with role '{u.role_name}' and access to gong planning for center(s) : {center_names}.")),
        cls="container",
    )
```

``` {.python #admin-page}

@rt('/admin')
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
            'center_has_planners': f'Cannot delete center. Center is still associated with users: {query_params.get("users", "")}. Please remove all planner associations first.'
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
        Div(
            H2("Users"),
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
                        Td(A("Delete", href=f"/delete_user/{u.email}", 
                             onclick="return confirm('Are you sure you want to delete this user?')"))
                    ) for u in users()]
                )
            )
        ),
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
            H2("Add New User"),
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
        ),
        Div(
            H2("Add New Center"),
            Form(
                Input(type="text", placeholder="Center Name", name="new_center_name", required=True),
                Input(type="text", placeholder="Gong DB Name (without .db)", name="new_gong_db_name", required=True),
                Small("The database file will be created as a copy of mahi.db"),
                Button("Add Center", type="submit"),
                method="post",
                action="/add_center"
            )
        ),
        Div(
            H2("Add New Planner"),
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
        ),

        cls="container",

    )
```

``` {.python #delete-routes}

@rt('/unfinished')
def unfinished():
    return Main(
        Nav(Li(A("Dashboard", href="/dashboard"))),
        Div(H1("This feature is not yet implemented.")),
        cls="container"
    )

@rt('/delete_user/{email}')
def delete_user(session, email: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        # Check if user has any planner associations
        user_planners = planners("user_email = ?", (email,))
        if user_planners:
            # Get the center names for the error message
            center_names = [p.center_name for p in user_planners]
            centers_list = ", ".join(center_names)
            return RedirectResponse(f'/admin?error=user_has_planners&centers={centers_list}')

        # If no planner associations, proceed with deletion
        db.execute("DELETE FROM users WHERE email = ?", (email,))
        return RedirectResponse('/admin?success=user_deleted')
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin"))),
            Div(H1("Error"), P(f"Could not delete user: {str(e)}")),
            cls="container"
        )

@rt('/delete_center/{center_name}')
def delete_center(session, center_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        # Get the center info to find the database file
        center_info = centers("center_name = ?", (center_name,))
        if not center_info:
            return RedirectResponse('/admin?error=center_not_found')

        # Check if center has any planner associations
        center_planners = planners("center_name = ?", (center_name,))
        if center_planners:
            # Get the user emails for the error message
            user_emails = [p.user_email for p in center_planners]
            users_list = ", ".join(user_emails)
            return RedirectResponse(f'/admin?error=center_has_planners&users={users_list}')

        gong_db_name = center_info[0].gong_db_name
        db_path = f'data/{gong_db_name}'

        # If no planner associations, proceed with deletion
        db.execute("DELETE FROM centers WHERE center_name = ?", (center_name,))

        # Finally, delete the associated database file if it exists
        if os.path.exists(db_path):
            os.remove(db_path)
            # Also remove any SQLite journal files
            for ext in ['-shm', '-wal']:
                journal_file = db_path + ext
                if os.path.exists(journal_file):
                    os.remove(journal_file)

        return RedirectResponse('/admin?success=center_deleted')
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin"))),
            Div(H1("Error"), P(f"Could not delete center: {str(e)}")),
            cls="container"
        )

@rt('/delete_planner/{user_email}/{center_name}')
def delete_planner(session, user_email: str, center_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        db.execute("DELETE FROM planners WHERE user_email = ? AND center_name = ?", (user_email, center_name))
        return RedirectResponse('/admin?success=planner_deleted')
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin"))),
            Div(H1("Error"), P(f"Could not delete planner association: {str(e)}")),
            cls="container"
        )
```

``` {.python #insert-routes}

@rt('/add_user')
def add_user(session, new_user_email: str, role_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    if not new_user_email or not role_name:
        return RedirectResponse('/admin?error=missing_fields')

    try:
        # Check if user already exists
        existing_user = users("email = ?", (new_user_email,))
        if existing_user:
            return RedirectResponse('/admin?error=user_exists')

        # Validate role
        if role_name not in ['admin', 'user']:
            return RedirectResponse('/admin?error=invalid_role')

        # Add new user
        users.insert(
            email=new_user_email,
            name=new_user_email.split('@')[0],  # Use email prefix as default name
            role_name=role_name,
            is_active=False,
            magic_link_token=None,
            magic_link_expiry=None
        )
        return RedirectResponse('/admin?success=user_added')
    except Exception as e:
        return RedirectResponse('/admin?error=database_error')

@rt('/add_center')
def add_center(session, new_center_name: str, new_gong_db_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    if not new_center_name or not new_gong_db_name:
        return RedirectResponse('/admin?error=missing_fields')

    try:
        # Check if center already exists
        existing_center = centers("center_name = ?", (new_center_name,))
        if existing_center:
            return RedirectResponse('/admin?error=center_exists')

        # Ensure gong_db_name ends with .db
        if not new_gong_db_name.endswith('.db'):
            new_gong_db_name += '.db'

        # Check if database file already exists
        db_path = f'data/{new_gong_db_name}'
        if os.path.exists(db_path):
            return RedirectResponse('/admin?error=db_file_exists')

        # Copy mahi.db as template for new center
        template_db = 'data/mahi.db'
        if not os.path.exists(template_db):
            return RedirectResponse('/admin?error=template_not_found')

        # Create the new database by copying mahi.db
        shutil.copy2(template_db, db_path)

        # Add new center to the centers table
        centers.insert(
            center_name=new_center_name,
            gong_db_name=new_gong_db_name
        )
        return RedirectResponse('/admin?success=center_added')
    except Exception as e:
        return RedirectResponse('/admin?error=database_error')

@rt('/add_planner')
def add_planner(session, new_planner_user_email: str, new_planner_center_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    if not new_planner_user_email or not new_planner_center_name:
        return RedirectResponse('/admin?error=missing_fields')

    try:
        # Check if user exists
        user_exists = users("email = ?", (new_planner_user_email,))
        if not user_exists:
            return RedirectResponse('/admin?error=user_not_found')

        # Check if center exists
        center_exists = centers("center_name = ?", (new_planner_center_name,))
        if not center_exists:
            return RedirectResponse('/admin?error=center_not_found')

        # Check if planner association already exists
        existing_planner = planners("user_email = ? AND center_name = ?", (new_planner_user_email, new_planner_center_name))
        if existing_planner:
            return RedirectResponse('/admin?error=planner_exists')

        # Add new planner association
        planners.insert(
            user_email=new_planner_user_email,
            center_name=new_planner_center_name
        )
        return RedirectResponse('/admin?success=planner_added')
    except Exception as e:
        return RedirectResponse('/admin?error=database_error')
```
