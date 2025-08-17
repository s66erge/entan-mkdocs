# User pages

Will only be reachable for users who are signed in.

``` {.python #admin-change-md}

<<change-users>>
<<change-centers>>
<<change-planners>>
```

TODO document admin-change

``` {.python #change-users}

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
            return RedirectResponse(f'/admin_page?error=user_has_planners&centers={centers_list}')

        # If no planner associations, proceed with deletion
        db.execute("DELETE FROM users WHERE email = ?", (email,))
        return RedirectResponse('/admin_page?success=user_deleted')
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin_page"))),
            Div(H1("Error"), P(f"Could not delete user: {str(e)}")),
            cls="container"
        )

@rt('/add_user')
def post(session, new_user_email: str, role_name: str):
    print(f"email: {new_user_email}, role: {role_name}")
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    if not new_user_email or not role_name:
        return RedirectResponse('/admin_page?error=missing_fields')

    try:
        # Check if user already exists
        existing_user = users("email = ?", (new_user_email,))
        if existing_user:
            #return RedirectResponse('/admin_page?error=user_exists')
            return Div(feedback_to_user({"error": "user_exists"}))

        # Validate role
        if role_name not in ['admin', 'user']:
            return RedirectResponse('/admin_page?error=invalid_role')

        # Add new user
        users.insert(
            email=new_user_email,
            name=new_user_email.split('@')[0],  # Use email prefix as default name
            role_name=role_name,
            is_active=False,
            magic_link_token=None,
            magic_link_expiry=None
        )
        #return RedirectResponse('/admin_page?success=user_added')
        return Div(
            Div(feedback_to_user({"success": "user_added"})),
            Div(show_users_table(), hx_swap_oob="true", id="users-table"),
            Div(show_users_form(), hx_swap_oob="true", id="users-form")
        )
    except Exception as e:
        return RedirectResponse('/admin_page?error=database_error')
```

``` {.python #change-centers}

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
            return RedirectResponse('/admin_page?error=center_not_found')

        # Check if center has any planner associations
        center_planners = planners("center_name = ?", (center_name,))
        if center_planners:
            # Get the user emails for the error message
            user_emails = [p.user_email for p in center_planners]
            users_list = ", ".join(user_emails)
            return RedirectResponse(f'/admin_page?error=center_has_planners&users={users_list}')

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

        return RedirectResponse('/admin_page?success=center_deleted')
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin_page"))),
            Div(H1("Error"), P(f"Could not delete center: {str(e)}")),
            cls="container"
        )

@rt('/add_center')
def add_center(session, new_center_name: str, new_gong_db_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    if not new_center_name or not new_gong_db_name:
        return RedirectResponse('/admin_page?error=missing_fields')

    try:
        # Check if center already exists
        existing_center = centers("center_name = ?", (new_center_name,))
        if existing_center:
            return RedirectResponse('/admin_page?error=center_exists')

        # Ensure gong_db_name ends with .db
        if not new_gong_db_name.endswith('.db'):
            new_gong_db_name += '.db'

        # Check if database file already exists
        db_path = f'data/{new_gong_db_name}'
        if os.path.exists(db_path):
            return RedirectResponse('/admin_page?error=db_file_exists')

        # Copy mahi.db as template for new center
        template_db = 'data/mahi.db'
        if not os.path.exists(template_db):
            return RedirectResponse('/admin_page?error=template_not_found')

        # Create the new database by copying mahi.db
        shutil.copy2(template_db, db_path)

        # Add new center to the centers table
        centers.insert(
            center_name=new_center_name,
            gong_db_name=new_gong_db_name
        )
        return RedirectResponse('/admin_page?success=center_added')
    except Exception as e:
        return RedirectResponse('/admin_page?error=database_error')
```

``` {.python #change-planners}

@rt('/delete_planner/{user_email}/{center_name}')
def delete_planner(session, user_email: str, center_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        # Check how many planners are associated with this center
        center_planners = planners("center_name = ?", (center_name,))

        # If this is the only planner for this center, prevent deletion
        if len(center_planners) <= 1:
            return RedirectResponse(f'/admin_page?error=last_planner_for_center&center={center_name}')

        # If there are other planners for this center, proceed with deletion
        db.execute("DELETE FROM planners WHERE user_email = ? AND center_name = ?", (user_email, center_name))
        return RedirectResponse('/admin_page?success=planner_deleted')
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin_page"))),
            Div(H1("Error"), P(f"Could not delete planner association: {str(e)}")),
            cls="container"
        )

@rt('/add_planner')
def add_planner(session, new_planner_user_email: str, new_planner_center_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    if not new_planner_user_email or not new_planner_center_name:
        return RedirectResponse('/admin_page?error=missing_fields')

    try:
        # Check if user exists
        user_exists = users("email = ?", (new_planner_user_email,))
        if not user_exists:
            return RedirectResponse('/admin_page?error=user_not_found')

        # Check if center exists
        center_exists = centers("center_name = ?", (new_planner_center_name,))
        if not center_exists:
            return RedirectResponse('/admin_page?error=center_not_found')

        # Check if planner association already exists
        existing_planner = planners("user_email = ? AND center_name = ?", (new_planner_user_email, new_planner_center_name))
        if existing_planner:
            return RedirectResponse('/admin_page?error=planner_exists')

        # Add new planner association
        planners.insert(
            user_email=new_planner_user_email,
            center_name=new_planner_center_name
        )
        return RedirectResponse('/admin_page?success=planner_added')
    except Exception as e:
        return RedirectResponse('/admin_page?error=database_error')
```
