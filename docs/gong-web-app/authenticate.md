# Authentication

This is a passwordless authentication:

- The user enters their email on a website
- The website generates a random string (a "token") and saves it together with the user's email into a database
- The website sends an email to the user with a link that encodes the generated token
- The user clicks on the link
- The website looks for a record in the users database table with the token from the link
- If it can find a record, the user will be logged in (again by storing information in the session)

``` {.python #authentication}

<<build-serve-login-form>>
<<handling-form>>
<<send-link>>
<<verify-token>>
<<logout>>
```

### Login form

The actual form element is extracted into a MyForm() function. Its not really needed this time, since we don't use it a second time!

``` {.python #build-serve-login-form}
def signin_form():
   return Form(
       Div(
           Div(
               Input(id='email', type='email', placeholder='foo@bar.com'),
           ),
       ),
       Button("Sign In with Email", type="submit", id="submit-btn"),
       hx_post="/create_magic_link",
       hx_target="#error",
       hx_disabled_elt="#submit-btn"
   )

@rt('/login')
def get():   
   return Main(
       Div(
           H1("Sign In"),
           P("Enter your email to sign in to The App."),
           Div(signin_form(), id='login_form'),
           P(id="error")
       ), cls="container"
   )
```

### Handling the login form

This handler first checks if the email is present. If its not, it returns an error that will be swapped into the #error paragraph in the form by HTMX, just like last time.

We create a magic_link_token using the secrets package from the python standard library. This token is a 32 characters long string. Also we generate an expiry date, which lies 15 minutes in the future.

The token should only be valid for a certain amount of time to increase the security of the authentication system.

Then it tries to find a user with the given email and if there is no user with this email, the IndexError is raised and it returns an error like above.

Another option would be to create a new user now by replacing:

```
return "Email is not registered ..."
```

with:

```
user = User(email=email, is_active=False, magic_link_token=magic_link_token, magic_link_expiry=magic_link_expiry)
users.insert(user)
```

Then we update the user row in the database with the expiration date and the token itself.

Then we create the login link by adding the token to the base url.
If we are from Railway production, os.name == 'posix' and the base URL is saved in the RAILWAY_PUBLIC_DOMAIN environment variable.
If we are running locally (os.name == 'nt'), directly or within railway CLI, the base URL is http://localhost:5001.

If everything went well, we return a success message to the user. Remember, the form has been defined to swap the content of the #error paragraph. Since I want to change the appearance of the text we send back, I also send back a HX-Reswap header with the value outerHTML. This tells HTMX to swap the outer HTML of the #error html element with the content we send back, a paragraph tag with the success message.

Also I want to disable the submit button and show a message that the magic link has been sent. To do this, we use one of the most powerful features of HTMX, out-of-band swaps. In HTMX you can update more than one piece of UI by setting the hx-swap-oob attribute to true on an element. HTMX will then swap in the returned element at the location of the element with the same id (#submit-btn in this case). You can read more about HTMX's out-of-band swaps [here](https://htmx.org/docs/#oob_swaps).

``` {.python #handling-form}

@rt('/create_magic_link')
def post(email: str):
    if not email:
       return (feedback_to_user({'error': 'missing_email'}))

    magic_link_token = secrets.token_urlsafe(32)
    magic_link_expiry = datetime.now() + timedelta(minutes=15)
    try:
       user = users[email]
       users.update(email= email, magic_link_token= magic_link_token, magic_link_expiry= magic_link_expiry)
    except NotFoundError:
        return Div(
            (feedback_to_user({'error': 'not_registered', 'email': f"{email}"})),
            Div(signin_form(), hx_swap_oob="true", id="login_form")
        )
    domainame = os.environ.get('RAILWAY_PUBLIC_DOMAIN', None)

    if (not isa_dev_computer()) and (domainame is not None):
        base_url = 'https://' + os.environ.get('RAILWAY_PUBLIC_DOMAIN')
    else: 
        print(" machine name: " + socket.gethostname())
        base_url = 'http://localhost:5001'

    magic_link = f"{base_url}/verify_magic_link/{magic_link_token}"
    send_magic_link_email(email, magic_link)

    return P(feedback_to_user({'success': 'magic_link_sent'}), id="success"),
    HttpHeader('HX-Reswap', 'outerHTML'), Button("Magic link sent", type="submit", id="submit-btn", disabled=True, hx_swap_oob="true")
```


### Send the magic link

Now we only need to send an email to the user with the link.
The link then sends a get request to the /verify_magic_link/{token} endpoint.

In production mode - remote or local within railway CLI -, we can use the smtplib via send_email (in utilities.md) to send an email using Gmail's SMTP server. 

In dev mode, lets just mock sending the email by printing the email content to the console.

``` {.python #send-link}

def send_magic_link_email(email_address: str, magic_link: str):

   email_subject = "Sign in to The App"
   email_text = f"""
   Hey there,

   Click this link to sign in to The App: {magic_link}

   If you didn't request this, just ignore this email.

   Cheers,
   The App Team
   """
   email_sender = os.environ.get('GOOGLE_SMTP_USER','None')
   if email_sender == 'None':
       print(f'To: {email_address}\n Subject: {email_subject}\n\n{email_text}')
   else:
       send_email(email_subject, email_text, [email_address])
```

### Authenticate the user

We save the current time into the variable now, because we need to look whether the token is already expired. Then we retrieve the first item with the specified token and an expiration date that lies in the future from the users table.

There should only be one or no user coming back from this query, so we wrap this whole code in a try/catch block.

If a user has been found using this query, we will save his or hers email in the auth key of our session dictionary. If its the first time the user logs in, we set is_active to true for this database record.

We do this to keep our database clean. Imagine a hacker enters thousands of random email addresses into our beautiful sign in form and therefore creates thousands of records in our database. To keep our database clean, we can use this is_active column to delete all inactive database records periodically using cron jobs.

``` {.python #verify-token}

@rt('/verify_magic_link/{token}')
def get(session, token: str):
   nowstr = f"'{datetime.now()}'"
   try:
       user = users("magic_link_token = ? AND magic_link_expiry > ?", (token, nowstr))[0]
       session['auth'] = user.email
       users.update(email= user.email, magic_link_token= None, magic_link_expiry= None, is_active= True)
       return RedirectResponse('/dashboard')
   except IndexError:
       return "Invalid or expired magic link"
```

### Beforeware to restrict access

We need a page that is only accessible for authenticated users and a mechanism to restrict the access to this page for non-authenticated users. We will use FastHTMLs concept of beforeware for restricting access.

Here we define a function called before that takes in the request and saves whatever in the auth key of the session into the auth variable as well as the scope of the request. The request scope is something that comes from ASGI, the underlying webserver technology of FastHTML. Think of it as a kind of metadata or context of the request.

If there is nothing in session["auth"], auth will evaluate to False and we will redirect the user to the login page.

Then well define a Beforeware object with our newly defined before function. This will make sure that every request runs first through our function, unless its targeting one of the paths we define in the skip list. Everything else will be guarded by this Beforeware. Now we just need to pass our newly created Beforeware class to our fast_app function as the beforeware argument:

app, rt = fast_app(..., before=bware)

``` {.python #auth-beforeware}

login_redir = RedirectResponse('/login', status_code=303)

def before(req, session):
   auth = req.scope['auth'] = session.get('auth', None)
   if not auth: return login_redir

bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login','/', '/create_magic_link', r'/verify_magic_link/.*'])
```

``` {.python #logout}
@rt('/logout')
def post(session):
    del session['auth']
    return HttpHeader('HX-Redirect', '/login')
```
