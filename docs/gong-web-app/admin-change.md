# Admin change functions

Used by the admin page (`<<admin-show>>` in admin-show.md):  
functions to add or delete a user / center / planner.

All these functions are called with these htmx ([intro](../architecture/ui-archi.md)) tags:  
- `hx_post=` route to the function  
- `hx_target=` id of DOM element where the resulting html will be placed  
and these functions can update multiple other DOM elements with `hx_swap_oob="true"`

``` {.python #admin-change}
<<delete-user>>
<<add-user>>
<<delete-center>>
<<add-center>>
<<delete-planner>>
<<add-planner>>
```

``` {.python #delete-user}

@rt('/delete_user/{email}')
@admin_required
def post(session, email: str):
    try:
        user_info = users("email = ?",(email,))
        user_planners = planners("user_email = ?", (email,))  ## [1]
        
        if not user_info:
            message = {'error' : 'user_not_found'}
       
        elif user_planners:  ## [1] 
            center_names = [p.center_name for p in user_planners]  ## [2]
            centers_list = ", ".join(center_names)
            message = {"error": "user_has_planners", "centers": f"{centers_list}"}

        else:  ## [3]
            db.execute("DELETE FROM users WHERE email = ?", (email,))
            message = {"success": "user_deleted"}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_users_table(), hx_swap_oob="true", id="users-table") if "success" in message else None,
            ## [4]
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form") if "success" in message else None
        )
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')
```
[1] Check if user has any planner associations  
[2] Get the center names for the error message  
[3] Proceed with deletion  
[4] rebuild the dropdown of the planners form to show changed users/centers
<br><br>

``` {.python #add-user}
@rt('/add_user')
@admin_required
def post(session, new_user_email: str = "", name: str = "",role_name: str =""):
    try:
        if new_user_email == "" or name == "" or role_name == "":
            message = {"error" : "missing_fields"}

        elif not roles("role_name = ?", (role_name,)):
            message = {"error": "invalid_role"}

        elif users("email = ?", (new_user_email,)):
            message = {"error": "user_exists"}

        else:  ## [1]
            users.insert(
            email=new_user_email,
            name=name,
            role_name=role_name,
            is_active=False,
            magic_link_token=None,
            magic_link_expiry=None
            )
            message = {"success": "user_added"}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_users_table(), hx_swap_oob="true", id="users-table") if "success" in message else None,
            Div(show_users_form(), hx_swap_oob="true", id="users-form"),
            ## [2]
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form") if "success" in message else None
        )
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')
```
[1] creates the new user  
[2] rebuild the dropdown of the planners form to show changed users/centers
<br><br> 

``` {.python #delete-center}

@rt('/delete_center/{center_name}')
@admin_required
def post(session, center_name: str):
    try:
        center_info = centers("center_name = ?", (center_name,))
        gong_db_name = center_info[0].gong_db_name  ## [1]
        db_path = f'data/{gong_db_name}'  ## [1]
        center_planners = planners("center_name = ?", (center_name,))  ## [2]

        if not center_info:
            message = {'error' : 'center_not_found'}

        elif center_planners:  ## [2]
            user_emails = [p.user_email for p in center_planners]  ## [3]
            users_list = ", ".join(user_emails)
            message = {'error' : 'center_has_planners','users' : f'{users_list}'}

        else:  ## [4]
            db.execute("DELETE FROM centers WHERE center_name = ?", (center_name,))
            if os.path.exists(db_path):
                os.remove(db_path)
                for ext in ['-shm', '-wal']:  ## [5]
                    journal_file = db_path + ext
                    if os.path.exists(journal_file):
                        os.remove(journal_file)
            message = {'success' : 'center_deleted'}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_centers_table(), hx_swap_oob="true", id="centers-table") if "success" in message else None,
            ## [6]
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form") if "success" in message else None
        )
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')

```
[1] get gong database path  
[2] check if center has planners  
[3] get planners emails for error message  
[4] delete the center and the associated database file if it exists  
[5] also remove any SQLite journal files  
[6] rebuild the dropdown of the planners form to show changed users/centers
<br><br>

``` {.python #add-center}

@rt('/add_center')
@admin_required
def post(session, new_center_name: str = "", new_gong_db_name: str = ""):
    ## [1]
    if not new_gong_db_name.endswith('.db'):
        new_gong_db_name += '.db'
    db_path = f'data/{new_gong_db_name}'
    template_db = 'data/mahi.db'

    try:
        if new_center_name == "" or new_gong_db_name == "":
            message = {"error" : "missing_fields"}

        elif centers("center_name = ?", (new_center_name,)):
            message = {"error" : "center_exists"}

        elif os.path.exists(db_path):
            message = {"error" : 'db_file_exists'}

        elif not os.path.exists(template_db):
            message = {'error' : 'template_not_found'}

        else:  ## [2]
            shutil.copy2(template_db, db_path)
            centers.insert(
                center_name=new_center_name,
                gong_db_name=new_gong_db_name
            )
            message = {'success': 'center_added'}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_centers_table(), hx_swap_oob="true", id="centers-table") if "success" in message else None,
            Div(show_centers_form(), hx_swap_oob="true", id="centers-form"),
            ## [3]
            Div(show_planners_form(), hx_swap_oob="true", id="planners-form") if "success" in message else None
        )
    except Exception as e:
        return Redirect(f'/db_error?etext={e}')
```
[1] Ensure gong_db_name ends with .db  
[2] Create the new database by copying mahi.db and update center table  
[3] rebuild the dropdown of the planners form to show changed users/center
<br><br>

``` {.python #delete-planner}

@rt('/delete_planner/{user_email}/{center_name}')
@admin_required
def post(session, user_email: str, center_name: str):
    try:
        center_planners = planners("center_name = ?", (center_name,))
        if len(center_planners) == 1:  ## [1]
            message ={"error" : "last_planner_for_center", "center" : f"{center_name}"}

        else:  ## [2]
            db.execute("DELETE FROM planners WHERE user_email = ? AND center_name = ?", (user_email, center_name))
            message = {"success" : "planner_deleted"}

        return Div(
            Div(feedback_to_user(message)),
            Div(show_planners_table(), hx_swap_oob="true", id="planners-table") if "success" in message else None
        )

    except Exception as e:
        return Redirect(f'/db_error?etext={e}')

```
[1] if this is the only planner for this center, prevent deletion
[2] proceed with deletion
<br><br>

``` {.python #add-planner}

@rt('/add_planner')
@admin_required
def post(session, new_planner_user_email: str = "", new_planner_center_name: str = ""):
    try:
        if new_planner_user_email == "" or new_planner_center_name == "":
            message = {"error" : "missing_fields"}

        elif not users("email = ?", (new_planner_user_email,)):
            message = {"error" : "user_not_found"}

        elif not centers("center_name = ?", (new_planner_center_name,)):
            message = {'error' : 'center_not_found'}

        elif planners("user_email = ? AND center_name = ?", (new_planner_user_email, new_planner_center_name)):
            message = {'error' : 'planner_exists'}

        else:  ## (1)
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
        return Redirect(f'/db_error?etext={e}')
```
(1) add planner association
<br><br>
