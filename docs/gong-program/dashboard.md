# User pages

Will only be reachable for users who are signed in.

``` {.python #start-admin-md}

<<dashboard>>
<<admin-page>>
<<delete-routes>>
<<insert-routes>>
```



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
def admin(session):
    sessemail = session['auth']
    u = users[sessemail]
    if u.role_name != "admin":
        return Main(
            Nav(Li(A("Dashboard", href="/dashboard"))),
            Div(H1("Access Denied"),
                P("You do not have permission to access this page.")),
            cls="container")
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
        Div(
            H2("Users"),
            Table(
                Thead(
                    Tr(Th("Email"), Th("Role"), Th("Action"))
                ),
                Tbody(
                    *[Tr(Td(u.email), Td(u.role_name), Td(A("Delete", href=f"/delete_user/{u.email}"))) for u in users()]
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
                    *[Tr(Td(c.center_name), Td(c.gong_db_name), Td(A("Delete", href=f"/delete_center/{c.center_name}"))) for c in centers()]
                )
            )
        ),
        Div(
            H2("Planners"),
            Table(
                Thead(
                    Tr(Th("User email"), Th("Center Name"), Th("Actions"))
                ),
                Tbody(
                    *[Tr(Td(p.user_email), Td(p.center_name), Td(A("Delete", href=f"/delete_planner/{p.user_email}/{p.center_name}"))) for p in planners()]
                )
            )
        ),
        Div(
            H2("Add New User"),
            Form(
                Input(type="email", placeholder="User Email", id="new_user_email"),
                Select( 
                    Option("Admin", value="admin"),
                    Option("User", value="user"),
                    id="new_user_role", name="role_name"),
                Button("Add User", hx_post="/add_user")
            )
        ),
        Div(
            H2("Add New Center"),
            Form(
                Input(type="text", placeholder="Center Name", id="new_center_name"),
                Input(type="text", placeholder="Gong DB Name", id="new_gong_db_name"),
                Button("Add Center", hx_post="/add_center")
            )
        ),
        Div(
            H2("Add New Planner"),
            Form(
                Input(type="text", placeholder="User email", id="new_planner_user_email"),
                Input(type="text", placeholder="Center Name", id="new_planner_center_name"),
                Button("Add Planner", hx_post="/add_planner")
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
def delete_user(email:str):
    return unfinished()

@rt('/delete_center/{center_name}')
def delete_center(center_name:str):
    return unfinished()

@rt('/delete_planner/{user_email}/{center_name}')
def delete_planner(user_email:str, center_name:str):
    return unfinished()
```

``` {.python #insert-routes}

@rt('/add_user')
def add_user():
    return HttpHeader('HX-Redirect', '/unfinished')

@rt('/add_center')
def add_center():   
    return HttpHeader('HX-Redirect', '/unfinished')

@rt('/add_planner')
def add_planner():  
    return HttpHeader('HX-Redirect', '/unfinished')          
```
