# The dashboard page


``` {.python #dashboard}

<<starting-page>>
```

### Starting page

Will only be reachable for users who are signed in.

``` {.python #starting-page}

@rt('/dashboard')
def get(session): 
    sessemail = session['auth']
    u = users("email = ?", (sessemail,))[0]
    centers = planners("userid = ?", (u.id,))
    center_names = ", ".join(c.center_name for c in centers)
    return Main(
        Nav(
            Ul(
                Li(A("Dashboard", href="#")),
                Li(A("About", href="#")),
                Li(A("Contact", href="#")),
            ),
            Button("Logout", hx_post="/logout"),
        ),
        Div(H1("Dashboard"), P(f"You are logged in as '{u.email}' with role '{u.role_name}' and access to gong planning for center(s) : {center_names}.")),
        cls="container",
    )
```

