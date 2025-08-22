# Admin change functions

Used by the admin page : admin-show.md

``` {.python #admin-change-md}

<<change-users>>
<<change-centers>>
<<change-planners>>
```

TODO document admin-change

``` {.python #change-users}

@rt('/delete_user/{email}') 
def post(session, email: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        user_info = users("email = ?",(email,))
        user_planners = planners("user_email = ?", (email,))
        
        if not user_info:
            message = {'error' : 'user_not_found'}
       
        # Check if user has any planner associations
        elif user_planners:
            # Get the center names for the error message
            center_names = [p.center_name for p in user_planners]
            centers_list = ", ".join(center_names)
            message = {"error": "user_has_planners", "centers": f"{centers_list}"}

        else:
            # If no planner associations, proceed with deletion
            db.execute("DELETE FROM users WHERE email = ?", (email,))
            message = {"success": "user_deleted"}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_users_table(), hx_swap_oob="true", id="users-table") if "success" in message else None
        )
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin_page"))),
            Div(H1("Error"), P(f"Could not delete user: {str(e)}")),
            cls="container"
        )

@rt('/add_user')
def post(session, new_user_email: str = "", name: str = "",role_name: str =""):
    # print(f"email: {new_user_email}, role: {role_name}")
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        if new_user_email == "" or name == "" or role_name == "":
            message = {"error" : "missing_fields"}

        # Validate role
        elif not roles("role_name = ?", (role_name,)):
            message = {"error": "invalid_role"}

        # Check if user already exists
        elif users("email = ?", (new_user_email,)):
            message = {"error": "user_exists"}

        # Add new user
        else:
            users.insert(
            email=new_user_email,
            name=name,  # Use email prefix as default name
            role_name=role_name,
            is_active=False,
            magic_link_token=None,
            magic_link_expiry=None
            )
            message = {"success": "user_added"}

        #return RedirectResponse('/admin_page?success=user_added')
        return Div(
            Div(feedback_to_user(message)),
            Div(show_users_table(), hx_swap_oob="true", id="users-table") if "success" in message else None,
            Div(show_users_form(), hx_swap_oob="true", id="users-form")
        )
    except Exception as e:
        #return RedirectResponse('/admin_page?error=database_error')
        return Div(
            Div(feedback_to_user({"error": "database_error"})),
            Div(show_users_form(), hx_swap_oob="true", id="users-form")
        )
```

``` {.python #change-centers}

@rt('/delete_center/{center_name}')
def delete_center(session, center_name: str):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        center_planners = planners("center_name = ?", (center_name,))
        # Get the center info to find the database file
        center_info = centers("center_name = ?", (center_name,))
        gong_db_name = center_info[0].gong_db_name
        db_path = f'data/{gong_db_name}'

        if not center_info:
            message = {'error' : 'center_not_found'}

        # Check if center has any planner associations
        elif center_planners:
            # Get the user emails for the error message
            user_emails = [p.user_email for p in center_planners]
            users_list = ", ".join(user_emails)
            message = {'error' : 'center_has_planners','users' : f'{users_list}'}

        else:
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
            message = {'success' : 'center_deleted'}

        # return RedirectResponse('/admin_page?success=center_deleted')
        return Div(
            Div(feedback_to_user(message)),
            Div(show_centers_table(), hx_swap_oob="true", id="centers-table") if "success" in message else None
        )
    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin_page"))),
            Div(H1("Error"), P(f"Could not delete center: {str(e)}")),
            cls="container"
        )

@rt('/add_center')
def add_center(session, new_center_name: str = "", new_gong_db_name: str = ""):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    # Ensure gong_db_name ends with .db
    if not new_gong_db_name.endswith('.db'):
        new_gong_db_name += '.db'
    db_path = f'data/{new_gong_db_name}'
    template_db = 'data/mahi.db'

    try:
        if new_center_name == "" or new_gong_db_name == "":
            message = {"error" : "missing_fields"}

        # Check if center already exists
        elif centers("center_name = ?", (new_center_name,)):
            message = {"error" : "center_exists"}

        # Check if database file already exists
        elif os.path.exists(db_path):
            message = {"error" : 'db_file_exists'}

        # Copy mahi.db as template for new center
        elif not os.path.exists(template_db):
            message = {'error' : 'template_not_found'}

        else:
            # Create the new database by copying mahi.db
            shutil.copy2(template_db, db_path)
            # Add new center to the centers table
            centers.insert(
                center_name=new_center_name,
                gong_db_name=new_gong_db_name
            )
            message = {'success': 'center_added'}

        # return RedirectResponse('/admin_page?success=center_added')
        return Div(
            Div(feedback_to_user(message)),
            Div(show_centers_table(), hx_swap_oob="true", id="centers-table") if "success" in message else None,
            Div(show_centers_form(), hx_swap_oob="true", id="centers-form")
        )
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
            message ={"error" : "last_planner_for_center", "center" : f"{center_name}"}
        else:
            # If there are other planners for this center, proceed with deletion
            db.execute("DELETE FROM planners WHERE user_email = ? AND center_name = ?", (user_email, center_name))
            message = {"success" : "planner_deleted"}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_planners_table(), hx_swap_oob="true", id="planners-table") if "success" in message else None
        )

    except Exception as e:
        return Main(
            Nav(Li(A("Admin", href="/admin_page"))),
            Div(H1("Error"), P(f"Could not delete planner association: {str(e)}")),
            cls="container"
        )

@rt('/add_planner')
def add_planner(session, new_planner_user_email: str = "", new_planner_center_name: str = ""):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return RedirectResponse('/dashboard')

    try:
        if new_planner_user_email == "" or new_planner_center_name == "":
            message = {"error" : "missing_fields"}

        # Check if user exists
        elif not users("email = ?", (new_planner_user_email,)):
            message = {"error" : "user_not_found"}

        # Check if center exists
        elif not centers("center_name = ?", (new_planner_center_name,)):
            message = {'error' : 'center_not_found'}

        # Check if planner association already exists
        elif planners("user_email = ? AND center_name = ?", (new_planner_user_email, new_planner_center_name)):
            message = {'error' : 'planner_exists'}

        # Add new planner association
        else:
            planners.insert(
            user_email=new_planner_user_email,
            center_name=new_planner_center_name
            )
            message = {'success' : 'planner_added'}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_planners_table(), hx_swap_oob="true", id="planners-table") if "success" in message else None,
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form")
        )
    except Exception as e:
        return RedirectResponse('/admin_page?error=database_error')
```
