# FastHTML

FastHTML is a python library which brings together Starlette, Uvicorn, HTMX, and fastcore&#39;s `FT` "FastTags" into a library for creating server-rendered hypermedia applications. The `FastHTML` class itself inherits from `Starlette`, and adds decorator-based routing with many additions, Beforeware, automatic `FT` to HTML rendering, and much more.'>

Things to remember when writing FastHTML apps:

- Although parts of its API are inspired by FastAPI, it is *not* compatible with FastAPI syntax and is not targeted at creating API services
- FastHTML includes support for Pico CSS and the fastlite sqlite library, although using both are optional; sqlalchemy can be used directly or via the fastsql library, and any CSS framework can be used. Support for the Surreal and css-scope-inline libraries are also included, but both are optional
- FastHTML is compatible with JS-native web components and any vanilla JS library, but not with React, Vue, or Svelte
- Use `serve()` for running uvicorn (`if __name__ == "__main__"` is not needed since it's automatic)
- When a title is needed with a response, use `Titled`; note that that already wraps children in `Container`, and already includes both the meta title as well as the H1 element.

# FastHTML quick start

A brief overview of many FastHTML features

## Installation

``` bash {.line-numbers}
pip install python-fasthtml
```

## A Minimal Application

A minimal FastHTML application looks something like this:

<div class="code-with-filename">

**main.py**

``` python {.line-numbers}
from fasthtml.common import *

app, rt = fast_app()

@rt("/")
def get():
    return Titled("FastHTML", P("Let's do this!"))

serve()
```

</div>

Line 1  
We import what we need for rapid development! A carefully-curated set of FastHTML functions and other Python objects is brought into our global namespace for convenience.

Line 3  
We instantiate a FastHTML app with the `fast_app()` utility function. This provides a number of really useful defaults that we’ll take advantage of later in the tutorial.

Line 5  
We use the `rt()` decorator to tell FastHTML what to return when a user visits `/` in their browser.

Line 6  
We connect this route to HTTP GET requests by defining a view function called `get()`.

Line 7  
A tree of Python function calls that return all the HTML required to write a properly formed web page. You’ll soon see the power of this approach.

Line 9  
The [serve()](https://AnswerDotAI.github.io/fasthtml/api/core.html#serve) utility configures and runs FastHTML using a library called `uvicorn`.

Run the code:

``` bash {.line-numbers}
python main.py
```

The terminal will look like this:

``` bash {.line-numbers}
INFO:     Uvicorn running on http://0.0.0.0:5001 (Press CTRL+C to quit)
INFO:     Started reloader process [58058] using WatchFiles
INFO:     Started server process [58060]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

Confirm FastHTML is running by opening your web browser to [127.0.0.1:5001](http://127.0.0.1:5001). You should see something like the image below:

![](quickstart-web-dev/quickstart-fasthtml.png)

<div>

> **Note**
>
> While some linters and developers will complain about the wildcard import, it is by design here and perfectly safe. FastHTML is very deliberate about the objects it exports in `fasthtml.common`. If it bothers you, you can import the objects you need individually, though it will make the code more verbose and less readable.
>
> If you want to learn more about how FastHTML handles imports, we cover that [here](https://docs.fastht.ml/explains/faq.html#why-use-import).

</div>

## A Minimal Charting Application

The [Script](https://AnswerDotAI.github.io/fasthtml/api/xtend.html#script) function allows you to include JavaScript. You can use Python to generate parts of your JS or JSON like this:

``` python {.line-numbers}
import json
from fasthtml.common import * 

app, rt = fast_app(hdrs=(Script(src="https://cdn.plot.ly/plotly-2.32.0.min.js"),))

data = json.dumps({
    "data": [{"x": [1, 2, 3, 4],"type": "scatter"},
            {"x": [1, 2, 3, 4],"y": [16, 5, 11, 9],"type": "scatter"}],
    "title": "Plotly chart in FastHTML ",
    "description": "This is a demo dashboard",
    "type": "scatter"
})


@rt("/")
def get():
  return Titled("Chart Demo", Div(id="myDiv"),
    Script(f"var data = {data}; Plotly.newPlot('myDiv', data);"))

serve()
```

## Debug Mode

When we can’t figure out a bug in FastHTML, we can run it in `DEBUG` mode. When an error is thrown, the error screen is displayed in the browser. This error setting should never be used in a deployed app.

``` python {.line-numbers}
from fasthtml.common import *

app, rt = fast_app(debug=True)

@rt("/")
def get():
    1/0
    return Titled("FastHTML Error!", P("Let's error!"))

serve()
```

Line 3  
`debug=True` sets debug mode on.

Line 7  
Python throws an error when it tries to divide an integer by zero.

## Routing

FastHTML builds upon FastAPI’s friendly decorator pattern for specifying URLs, with extra features:

<div class="code-with-filename">

**main.py**

``` python {.line-numbers}
from fasthtml.common import * 

app, rt = fast_app()

@rt("/")
def get():
  return Titled("FastHTML", P("Let's do this!"))

@rt("/hello")
def get():
  return Titled("Hello, world!")

serve()
```

</div>

Line 5  
The “/” URL on line 5 is the home of a project. This would be accessed at [127.0.0.1:5001](http://127.0.0.1:5001).

Line 9  
“/hello” URL on line 9 will be found by the project if the user visits [127.0.0.1:5001/hello](http://127.0.0.1:5001/hello).

<div>

> **Tip**
>
> It looks like `get()` is being defined twice, but that’s not the case.
> Each function decorated with `rt` is totally separate, and is injected into the router. We’re not calling them in the module’s namespace (`locals()`). Rather, we’re loading them into the routing mechanism using the `rt` decorator.

</div>

You can do more! Read on to learn what we can do to make parts of the URL dynamic.

## Variables in URLs

You can add variable sections to a URL by marking them with `{variable_name}`. Your function then receives the `{variable_name}` as a keyword argument, but only if it is the correct type. Here’s an example:

<div class="code-with-filename">

**main.py**

``` python {.line-numbers}
from fasthtml.common import * 

app, rt = fast_app()

@rt("/{name}/{age}")
def get(name: str, age: int):
  return Titled(f"Hello {name.title()}, age {age}")

serve()
```

</div>

Line 5  
We specify two variable names, `name` and `age`.

Line 6  
We define two function arguments named identically to the variables. You will note that we specify the Python types to be passed.

Line 7  
We use these functions in our project.

Try it out by going to this address:
[127.0.0.1:5001/uma/5](http://127.0.0.1:5001/uma/5). You should get a page that says,

> “Hello Uma, age 5”.

### What happens if we enter incorrect data?

The [127.0.0.1:5001/uma/5](http://127.0.0.1:5001/uma/5) URL works because `5` is an integer. If we enter something that is not, such as [127.0.0.1:5001/uma/five](http://127.0.0.1:5001/uma/five), then FastHTML will return an error instead of a web page.

<div>

> **FastHTML URL routing supports more complex types**
>
> The two examples we provide here use Python’s built-in `str` and `int` types, but you can use your own types, including more complex ones such as those defined by libraries like [attrs](https://pypi.org/project/attrs/), [pydantic](https://pypi.org/project/pydantic/), and even [sqlmodel](https://pypi.org/project/sqlmodel/).

</div>

## HTTP Methods

FastHTML matches function names to HTTP methods. So far the URL routes we’ve defined have been for HTTP GET methods, the most common method for web pages.

Form submissions often are sent as HTTP POST. When dealing with more dynamic web page designs, also known as Single Page Apps (SPA for short), the need can arise for other methods such as HTTP PUT and HTTP DELETE. The way FastHTML handles this is by changing the function name.

<div class="code-with-filename">

**main.py**

``` python {.line-numbers}
from fasthtml.common import * 

app, rt = fast_app()

@rt("/")  
def get():
  return Titled("HTTP GET", P("Handle GET"))

@rt("/")  
def post():
  return Titled("HTTP POST", P("Handle POST"))

serve()
```

</div>

Line 6  
On line 6 because the `get()` function name is used, this will handle HTTP GETs going to the `/` URI.

Line 10  
On line 10 because the `post()` function name is used, this will handle HTTP POSTs going to the `/` URI.

## CSS Files and Inline Styles

Here we modify default headers to demonstrate how to use the [Sakura CSS microframework](https://github.com/oxalorg/sakura) instead of FastHTML’s default of Pico CSS.

<div class="code-with-filename">

**main.py**

``` python {.line-numbers} 
from fasthtml.common import * 

app, rt = fast_app(
    pico=False,
    hdrs=(
        Link(rel='stylesheet', href='assets/normalize.min.css', type='text/css'),
        Link(rel='stylesheet', href='assets/sakura.css', type='text/css'),
        Style("p {color: red;}")
))

@app.get("/")
def home():
    return Titled("FastHTML",
        P("Let's do this!"),
    )

serve()
```

</div>

Line 4  
By setting `pico` to `False`, FastHTML will not include `pico.min.css`.

Line 7  
This will generate an HTML `<link>` tag for sourcing the css for Sakura.

Line 8  
If you want an inline styles, the
[Style()](https://AnswerDotAI.github.io/fasthtml/api/xtend.html#style) function will put the result into the HTML.

## Other Static Media File Locations

As you saw, [Script](https://AnswerDotAI.github.io/fasthtml/api/xtend.html#script) and `Link` are specific to the most common static media use cases in web apps: including JavaScript, CSS, and images. But it also works with videos and other static media files. The default behavior is to look for these files in the root directory - typically we don’t do anything special to include them. We can change the default directory that is looked in for files by adding the `static_path` parameter to the `fast_app` function.

``` python {.line-numbers}
app, rt = fast_app(static_path='public')
```

FastHTML also allows us to define a route that uses `FileResponse` to serve the file at a specified path. This is useful for serving images, videos, and other media files from a different directory without having to change the paths of many files. So if we move the directory containing the media files, we only need to change the path in one place. In the example below, we call images from a directory called `public`.

``` python {.line-numbers}
@rt("/{fname:path}.{ext:static}")
async def get(fname:str, ext:str): 
    return FileResponse(f'public/{fname}.{ext}')
```

## Rendering Markdown

``` python {.line-numbers}
from fasthtml.common import *

hdrs = (MarkdownJS(), HighlightJS(langs=['python', 'javascript', 'html', 'css']), )

app, rt = fast_app(hdrs=hdrs)

content = """
Here are some _markdown_ elements.

- This is a list item
- This is another list item
- And this is a third list item

**Fenced code blocks work here.**
"""

@rt('/')
def get(req):
    return Titled("Markdown rendering example", Div(content,cls="marked"))

serve()
```

## Code highlighting

Here’s how to highlight code without any markdown configuration.

``` python {.line-numbers}
from fasthtml.common import *

# Add the HighlightJS built-in header
hdrs = (HighlightJS(langs=['python', 'javascript', 'html', 'css']),)

app, rt = fast_app(hdrs=hdrs)

code_example = """
import datetime
import time

for i in range(10):
    print(f"{datetime.datetime.now()}")
    time.sleep(1)
"""

@rt('/')
def get(req):
    return Titled("Markdown rendering example",
        Div(
            # The code example needs to be surrounded by
            # Pre & Code elements
            Pre(Code(code_example))
    ))

serve()
```

## Defining new `ft` components

We can build our own `ft` components and combine them with other components. The simplest method is defining them as a function.

``` python {.line-numbers}
from fasthtml.common import *
```

``` python {.line-numbers}
def hero(title, statement):
    return Div(H1(title),P(statement), cls="hero")

# usage example
Main(
    hero("Hello World", "This is a hero statement")
)
```

``` html {.line-numbers}
<main>  <div class="hero">
    <h1>Hello World</h1>
    <p>This is a hero statement</p>
  </div>
</main>
```

### Pass through components

For when we need to define a new component that allows zero-to-many components to be nested within them, we lean on Python’s `*args` and `**kwargs` mechanism. Useful for creating page layout controls.

``` python {.line-numbers}
def layout(*args, **kwargs):
    """Dashboard layout for all our dashboard views"""
    return Main(
        H1("Dashboard"),
        Div(*args, **kwargs),
        cls="dashboard",
    )

# usage example
layout(
    Ul(*[Li(o) for o in range(3)]),
    P("Some content", cls="description"),
)
```

``` html {.line-numbers}
<main class="dashboard">  <h1>Dashboard</h1>
  <div>
    <ul>
      <li>0</li>
      <li>1</li>
      <li>2</li>
    </ul>
    <p class="description">Some content</p>
  </div>
</main>
```

### Dataclasses as ft components

While functions are easy to read, for more complex components some might find it easier to use a dataclass.

``` python {.line-numbers}
from dataclasses import dataclass

@dataclass
class Hero:
    title: str
    statement: str
    
    def __ft__(self):
        """ The __ft__ method renders the dataclass at runtime."""
        return Div(H1(self.title),P(self.statement), cls="hero")
    
# usage example
Main(
    Hero("Hello World", "This is a hero statement")
)
```

``` html {.line-numbers}
<main>  <div class="hero">
    <h1>Hello World</h1>
    <p>This is a hero statement</p>
  </div>
</main>
```

## Testing views in notebooks

Because of the ASGI event loop it is currently impossible to run FastHTML inside a notebook. However, we can still test the output of our views. To do this, we leverage Starlette, an ASGI toolkit that FastHTML uses.

``` python {.line-numbers}
# First we instantiate our app, in this case we remove the
# default headers to reduce the size of the output.
app, rt = fast_app(default_hdrs=False)

# Setting up the Starlette test client
from starlette.testclient import TestClient
client = TestClient(app)

# Usage example
@rt("/")
def get():
    return Titled("FastHTML is awesome", 
        P("The fastest way to create web apps in Python"))

print(client.get("/").text)
```

    <!doctype html>
    <html>
    <head>
        <title>FastHTML is awesome</title> 
    </head>
    <body>
        <main class="container">
           <h1>FastHTML is awesome</h1>
           <p>The fastest way to create web apps in Python</p>
        </main>
     </body>
     </html>

## Forms

To validate data coming from users, first define a dataclass representing the data you want to check. Here’s an example representing a signup form.

``` python {.line-numbers}
from dataclasses import dataclass

@dataclass
class Profile: email:str; phone:str; age:int
```

Create an FT component representing an empty version of that form. Don’t pass in any value to fill the form, that gets handled later.

``` python {.line-numbers}
profile_form = Form(method="post", action="/profile")(
        Fieldset(
            Label('Email', Input(name="email")),
            Label("Phone", Input(name="phone")),
            Label("Age", Input(name="age")),
        ),
        Button("Save", type="submit"),
    )
profile_form
```

``` html {.line-numbers}
<form enctype="multipart/form-data" method="post" action="/profile">
<fieldset>
<label>Email      <input name="email"></label>
<label>Phone      <input name="phone"></label>
<label>Age      <input name="age"></label>
</fieldset>
<button type="submit">Save</button>
</form>
```

Once the dataclass and form function are completed, we can add data to the form. To do that, instantiate the profile dataclass:

``` python {.line-numbers}
profile = Profile(email='john@example.com', phone='123456789', age=5)
profile
```

    Profile(email='john@example.com', phone='123456789', age=5)

Then add that data to the `profile_form` using FastHTML’s [fill_form](https://AnswerDotAI.github.io/fasthtml/api/components.html#fill_form) class:

``` python {.line-numbers}
fill_form(profile_form, profile)
```

``` html {.line-numbers}
<form enctype="multipart/form-data" method="post" action="/profile">
<fieldset>
<label>Email      <input name="email" value="john@example.com"></label>
<label>Phone      <input name="phone" value="123456789"></label>
<label>Age      <input name="age" value="5"></label>
</fieldset>
<button type="submit">Save</button>
</form>
```

### Forms with views

The usefulness of FastHTML forms becomes more apparent when they are combined with FastHTML views. We’ll show how this works by using the test client from above. First, let’s create a SQlite database:

``` python {.line-numbers}
db = database("profiles.db")
profiles = db.create(Profile, pk="email")
```

Now we insert a record into the database:

``` python {.line-numbers}
profiles.insert(profile)
```

    Profile(email='john@example.com', phone='123456789', age=5)

And we can then demonstrate in the code that form is filled and displayed to the user.

``` python {.line-numbers}
@rt("/profile/{email}")
def profile(email:str):
    profile = profiles[email]
    filled_profile_form = fill_form(profile_form, profile)
    return Titled(f'Profile for {profile.email}', filled_profile_form)

print(client.get(f"/profile/john@example.com").text)
```

Line 3  
Fetch the profile using the profile table’s `email` primary key

Line 4  
Fill the form for display.


    <!doctype html>
    <html>
    <head>
        <title>Profile for john@example.com</title>   </head>
    <body>
    <main class="container">
    <h1>Profile for john@example.com</h1>
    <form enctype="multipart/form-data" method="post" action="/profile">
    <fieldset>
    <label>Email             <input name="email" value="john@example.com"> </label>
    <label>Phone             <input name="phone" value="123456789"></label>
    <label>Age             <input name="age" value="5"></label>
    </fieldset>
    <button type="submit">Save</button></form></main>   </body>
    </html>

And now let’s demonstrate making a change to the data.

``` python {.line-numbers}
@rt("/profile")
def post(profile: Profile):
    profiles.update(profile)
    return RedirectResponse(url=f"/profile/{profile.email}")

new_data = dict(email='john@example.com', phone='7654321', age=25)
print(client.post("/profile", data=new_data).text)
```

Line 2  
We use the `Profile` dataclass definition to set the type for the
incoming `profile` content. This validates the field types for the
incoming data

Line 3  
Taking our validated data, we updated the profiles table

Line 4  
We redirect the user back to their profile view

Line 7  
The display is of the profile form view showing the changes in data.


    <!doctype html>
    <html>
       <head>
    <title>Profile for john@example.com</title>   </head>
    <body>
    <main class="container">
    <h1>Profile for john@example.com</h1>
    <form enctype="multipart/form-data" method="post" action="/profile">
    <fieldset>
    <label>Email             <input name="email" value="john@example.com"> </label>
    <label>Phone             <input name="phone" value="7654321"> </label>
    <label>Age             <input name="age" value="25"></label>
    </fieldset>
    <button type="submit">Save</button></form></main>
    </body>
    </html>

## Strings and conversion order

The general rules for rendering are: - `__ft__` method will be called (for default components like `P`, `H2`, etc. or if you define your own components) - If you pass a string, it will be escaped - On other python objects, `str()` will be called

As a consequence, if you want to include plain HTML tags directly into e.g. a `Div()` they will get escaped by default (as a security measure to avoid code injections). This can be avoided by using `NotStr()`, a convenient way to reuse python code that returns already HTML.

If you use pandas, you can use `pandas.DataFrame.to_html()` to get a nice table. To include the output a FastHTML, wrap it in `NotStr()`, like `Div(NotStr(df.to_html()))`.

Above we saw how a dataclass behaves with the `__ft__` method defined. On a plain dataclass, `str()` will be called (but not escaped).

``` python {.line-numbers}
from dataclasses import dataclass

@dataclass
class Hero:
    title: str
    statement: str
        
# rendering the dataclass with the default method
Main(
    Hero("<h1>Hello World</h1>", "This is a hero statement")
)
```

``` html {.line-numbers}
<main>Hero(title='<h1>Hello World</h1>', statement='This is a hero statement')</main>
```

``` python {.line-numbers}
# This will display the HTML as text on your page
Div("Let's include some HTML here: <div>Some HTML</div>")
```

``` html {.line-numbers}
<div>Let&#x27;s include some HTML here: &lt;div&gt;Some HTML&lt;/div&gt;</div>
```

``` python {.line-numbers}
# Keep the string untouched, will be rendered on the page
Div(NotStr("<div><h1>Some HTML</h1></div>"))
```

``` html {.line-numbers}
<div><div><h1>Some HTML</h1></div></div>
```

## Custom exception handlers

FastHTML allows customization of exception handlers, but does so
gracefully. What this means is by default it includes all the `<html>` tags needed to display attractive content. Try it out!

``` python {.line-numbers}
from fasthtml.common import *

def not_found(req, exc): return Titled("404: I don't exist!")

exception_handlers = {404: not_found}

app, rt = fast_app(exception_handlers=exception_handlers)

@rt('/')
def get():
    return (Titled("Home page", P(A(href="/oops")("Click to generate 404 error"))))

serve()
```

We can also use lambda to make things more terse:

``` python {.line-numbers}
from fasthtml.common import *

exception_handlers={
    404: lambda req, exc: Titled("404: I don't exist!"),
    418: lambda req, exc: Titled("418: I'm a teapot!")
}

app, rt = fast_app(exception_handlers=exception_handlers)

@rt('/')
def get():
    return (Titled("Home page", P(A(href="/oops")("Click to generate 404 error"))))

serve()
```

## Cookies

We can set cookies using the [cookie()](https://AnswerDotAI.github.io/fasthtml/api/core.html#cookie) function. In our example, we’ll create a `timestamp` cookie.

``` python {.line-numbers}
from datetime import datetime
from IPython.display import HTML
```

``` python {.line-numbers}
@rt("/settimestamp")
def get(req):
    now = datetime.now()
    return P(f'Set to {now}'), cookie('now', datetime.now())

HTML(client.get('/settimestamp').text)
```

``` html {.line-numbers}
 <!doctype html>
 <html>
   <head>
     <title>FastHTML page</title>   
   </head>
   <body>
     <p>Set to 2024-09-26 15:33:48.141869</p>
   </body>
 </html>
 ```

Now let’s get it back using the same name for our parameter as the cookie name.

``` python {.line-numbers}
@rt('/gettimestamp')
def get(now:parsed_date): return f'Cookie was set at time {now.time()}'

client.get('/gettimestamp').text
```

    'Cookie was set at time 15:33:48.141903'

## Sessions

For convenience and security, FastHTML has a mechanism for storing small amounts of data in the user’s browser. We can do this by adding a `session` argument to routes. FastHTML sessions are Python dictionaries, and we can leverage to our benefit. The example below shows how to concisely set and get sessions.

``` python {.line-numbers}
@rt('/adder/{num}')
def get(session, num: int):
    session.setdefault('sum', 0)
    session['sum'] = session.get('sum') + num
    return Response(f'The sum is {session["sum"]}.')
```

## Toasts (also known as Messages)

Toasts, sometimes called “Messages” are small notifications usually in colored boxes used to notify users that something has happened. Toasts can be of four types:

- info
- success
- warning
- error

Examples toasts might include:

- “Payment accepted”
- “Data submitted”
- “Request approved”

Toasts require the use of the `setup_toasts()` function plus every view needs these two features:

- The session argument
- Must return FT components

``` python {.line-numbers}
setup_toasts(app)

@rt('/toasting')
def get(session):
    # Normally one toast is enough, this allows us to see
    # different toast types in action.
    add_toast(session, f"Toast is being cooked", "info")
    add_toast(session, f"Toast is ready", "success")
    add_toast(session, f"Toast is getting a bit crispy", "warning")
    add_toast(session, f"Toast is burning!", "error")
    return Titled("I like toast")
```

Line 1  
`setup_toasts` is a helper function that adds toast dependencies. Usually this would be declared right after `fast_app()`

Line 4  
Toasts require sessions

Line 11  
Views with Toasts must return FT or FtResponse components.

💡 `setup_toasts` takes a `duration` input that allows you to specify how long a toast will be visible before disappearing. For example `setup_toasts(duration=5)` sets the toasts duration to 5 seconds. By default toasts disappear after 10 seconds.

## Authentication and authorization

In FastHTML the tasks of authentication and authorization are handled with Beforeware. Beforeware are functions that run before the route handler is called. They are useful for global tasks like ensuring users are authenticated or have permissions to access a view.

First, we write a function that accepts a request and session arguments:

``` python {.line-numbers}
# Status code 303 is a redirect that can change POST to GET,
# so it's appropriate for a login page.
login_redir = RedirectResponse('/login', status_code=303)

def user_auth_before(req, sess):
    # The `auth` key in the request scope is automatically provided
    # to any handler which requests it, and can not be injected
    # by the user using query params, cookies, etc, so it should
    # be secure to use.    
    auth = req.scope['auth'] = sess.get('auth', None)
    # If the session key is not there, it redirects to the login page.
    if not auth: return login_redir
```

Now we pass our `user_auth_before` function as the first argument into a [Beforeware](https://AnswerDotAI.github.io/fasthtml/api/core.html#beforeware) class. We also pass a list of regular expressions to the `skip` argument, designed to allow users to still get to the home and login pages.

``` python {.line-numbers}
beforeware = Beforeware(
    user_auth_before,
    skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', r'.*\.js', '/login', '/']
)

app, rt = fast_app(before=beforeware)
```

## Server-sent events (SSE)

With [server-sent events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events), it’s possible for a server to send new data to a web page at any time, by pushing messages to the web page. Unlike WebSockets, SSE can only go in one direction: server to client. SSE is also part of the HTTP specification unlike WebSockets which uses its own specification.

FastHTML introduces several tools for working with SSE which are covered in the example below. While concise, there’s a lot going on in this function so we’ve annotated it quite a bit.

``` python {.line-numbers}
import random
from asyncio import sleep
from fasthtml.common import *

hdrs=(Script(src="https://unpkg.com/htmx-ext-sse@2.2.1/sse.js"),)
app,rt = fast_app(hdrs=hdrs)

@rt
def index():
    return Titled("SSE Random Number Generator",
        P("Generate pairs of random numbers, as the list grows scroll downwards."),
        Div(hx_ext="sse",
            sse_connect="/number-stream",
            hx_swap="beforeend show:bottom",
            sse_swap="message"))

shutdown_event = signal_shutdown()

async def number_generator():
    while not shutdown_event.is_set():
        data = Article(random.randint(1, 100))
        yield sse_message(data)
        await sleep(1)

@rt("/number-stream")
async def get(): return EventStream(number_generator())
```

Line 5  
Import the HTMX SSE extension

Line 12  
Tell HTMX to load the SSE extension

Line 13  
Look at the `/number-stream` endpoint for SSE content

Line 14  
When new items come in from the SSE endpoint, add them at the end of the current content within the div. If they go beyond the screen, scroll downwards

Line 15  
Specify the name of the event. FastHTML’s default event name is “message”. Only change if you have more than one call to SSE endpoints within a view

Line 17  
Set up the asyncio event loop

Line 19  
Don’t forget to make this an `async` function!

Line 20  
Iterate through the asyncio event loop

Line 22  
We yield the data. Data ideally should be comprised of FT components as that plugs nicely into HTMX in the browser

Line 26  
The endpoint view needs to be an async function that returns a [EventStream](https://AnswerDotAI.github.io/fasthtml/api/core.html#eventstream)

## Websockets

With websockets we can have bi-directional communications between a browser and client. Websockets are useful for things like chat and certain types of games. While websockets can be used for single direction messages from the server (i.e. telling users that a process is finished), that task is arguably better suited for SSE.

FastHTML provides useful tools for adding websockets to your pages.

```python {.line-numbers}

from fasthtml.common import *
from asyncio import sleep

app, rt = fast_app(exts='ws')

def mk_inp(): return Input(id='msg', autofocus=True)

@rt('/')
async def get(request):
    cts = Div(
        Div(id='notifications'),
        Form(mk_inp(), id='form', ws_send=True),
        hx_ext='ws', ws_connect='/ws')
    return Titled('Websocket Test', cts)

async def on_connect(send):
    print('Connected!')
    await send(Div('Hello, you have connected', id="notifications"))

async def on_disconnect(ws):
    print('Disconnected!')

@app.ws('/ws', conn=on_connect, disconn=on_disconnect)
async def ws(msg:str, send):
    await send(Div('Hello ' + msg, id="notifications"))
    await sleep(2)
    return Div('Goodbye ' + msg, id="notifications"), mk_inp()
```

Line 4  
To use websockets in FastHTML, you must instantiate the app with `exts` set to ‘ws’

Line 6  
As we want to use websockets to reset the form, we define the `mk_input` function that can be called from multiple locations

Line 12  
We create the form and mark it with the `ws_send` attribute, which is documented here in the [HTMX websocket specification](https://v1.htmx.org/extensions/web-sockets/). This tells HTMX to send a message to the nearest websocket based on the trigger for the form element, which for forms is pressing the `enter` key, an action
considered to be a form submission

Line 13  
This is where the HTMX extension is loaded (`hx_ext='ws'`) and the nearest websocket is defined (`ws_connect='/ws'`)

Line 16  
When a websocket first connects we can optionally have it call a function that accepts a `send` argument. The `send` argument will push a message to the browser.

Line 18  
Here we use the `send` function that was passed into the `on_connect` function to send a `Div` with an `id` of `notifications` that HTMX assigns to the element in the page that already has an `id` of `notifications`

Line 20  
When a websocket disconnects we can call a function which takes no arguments. Typically the role of this function is to notify the server to take an action. In this case, we print a simple message to the console

Line 23  
We use the `app.ws` decorator to mark that `/ws` is the route for our websocket. We also pass in the two optional `conn` and `disconn` parameters to this decorator. As a fun experiment, remove the `conn` and `disconn` arguments and see what happens

Line 24  
Define the `ws` function as async. This is necessary for ASGI to be able to serve websockets. The function accepts two arguments, a `msg` that is user input from the browser, and a `send` function for pushing data back to the browser

Line 25  
The `send` function is used here to send HTML back to the page. As the HTML has an `id` of `notifications`, HTMX will overwrite what is already on the page with the same ID

Line 27  
The websocket function can also be used to return a value. In this case, it is a tuple of two HTML elements. HTMX will take the elements and replace them where appropriate. As both have `id` specified (`notifications` and `msg` respectively), they will replace their predecessor on the page.

## File Uploads

A common task in web development is uploading files. The examples below
are for uploading files to the hosting server, with information about
the uploaded file presented to the user.

> **File uploads in production can be dangerous**
>
> File uploads can be the target of abuse, accidental or intentional.
> That means users may attempt to upload files that are too large or
> present a security risk. This is especially of concern for public
> facing apps. File upload security is outside the scope of this
> tutorial, for now we suggest reading the [OWASP File Upload Cheat
> Sheet](https://cheatsheetseries.owasp.org/cheatsheets/File_Upload_Cheat_Sheet.html).

### Single File Uploads

``` python {.line-numbers}
from fasthtml.common import *
from pathlib import Path

app, rt = fast_app()

upload_dir = Path("filez")
upload_dir.mkdir(exist_ok=True)

@rt('/')
def get():
    return Titled("File Upload Demo",
        Article(
            Form(hx_post=upload, hx_target="#result-one")(
                Input(type="file", name="file"),
                Button("Upload", type="submit", cls='secondary'),
            ),
            Div(id="result-one")
        )
    )

def FileMetaDataCard(file):
    return Article(
        Header(H3(file.filename)),
        Ul(
            Li('Size: ', file.size),            
            Li('Content Type: ', file.content_type),
            Li('Headers: ', file.headers),
        )
    )    

@rt
async def upload(file: UploadFile):
    card = FileMetaDataCard(file)
    filebuffer = await file.read()
    (upload_dir / file.filename).write_bytes(filebuffer)
    return card

serve()
```

Line 13  
Every form rendered with the [Form](https://AnswerDotAI.github.io/fasthtml/api/xtend.html#form) FT component defaults to `enctype="multipart/form-data"`

Line 14  
Don’t forget to set the `Input` FT Component’s type to `file`

Line 32  
The upload view should receive a [Starlette UploadFile](https://www.starlette.io/requests/#request-files) type. You can add other form variables

Line 33  
We can access the metadata of the card (filename, size, content_type, headers), a quick and safe process. We set that to the card variable

Line 34  
In order to access the contents contained within a file we use the `await` method to read() it. As files may be quite large or contain bad data, this is a seperate step from accessing metadata

Line 35  
This step shows how to use Python’s built-in `pathlib.Path` library to write the file to disk.

### Multiple File Uploads

``` python {.line-numbers}
from fasthtml.common import *
from pathlib import Path

app, rt = fast_app()

upload_dir = Path("filez")
upload_dir.mkdir(exist_ok=True)

@rt('/')
def get():
    return Titled("Multiple File Upload Demo",
        Article(
            Form(hx_post=upload_many, hx_target="#result-many")(
                Input(type="file", name="files", multiple=True),
                Button("Upload", type="submit", cls='secondary'),
            ),
            Div(id="result-many")
        )
    )

def FileMetaDataCard(file):
    return Article(
        Header(H3(file.filename)),
        Ul(
            Li('Size: ', file.size),            
            Li('Content Type: ', file.content_type),
            Li('Headers: ', file.headers),
        )
    )    

@rt
async def upload_many(files: list[UploadFile]):
    cards = []
    for file in files:
        cards.append(FileMetaDataCard(file))
        filebuffer = await file.read()
        (upload_dir / file.filename).write_bytes(filebuffer)
    return cards

serve()
```

Line 13  
Every form rendered with the [Form](https://AnswerDotAI.github.io/fasthtml/api/xtend.html#form) FT component defaults to `enctype="multipart/form-data"`

Line 14  
Don’t forget to set the `Input` FT Component’s type to `file` and assign the multiple attribute to `True`

Line 32  
The upload view should receive a `list` containing the [Starlette UploadFile](https://www.starlette.io/requests/#request-files) type. You can add other form variables

Line 34  
Iterate through the files

Line 35  
We can access the metadata of the card (filename, size, content_type, headers), a quick and safe process. We add that to the cards variable

Line 36  
In order to access the contents contained within a file we use the `await` method to read() it. As files may be quite large or contain bad data, this is a seperate step from accessing metadata

Line 37  
This step shows how to use Python’s built-in `pathlib.Path` library to write the file to disk.

# HTMX Reference

Brief description of all HTMX attributes, CSS classes, headers, events, extensions, js lib methods, and config options

## Contents

* [htmx Core Attributes](#attributes)
* [htmx Additional Attributes](#attributes-additional)
* [htmx CSS Classes](#classes)
* [htmx Request Headers](#request_headers)
* [htmx Response Headers](#response_headers)
* [htmx Events](#events)
* [htmx Extensions](/extensions)
* [JavaScript API](#api)
* [Configuration Options](#config)

## Core Attribute Reference {#attributes}

The most common attributes when using htmx.

<div class="info-table">

| Attribute                                        | Description                                                                                                        |
|--------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| [`hx-get`](@/attributes/hx-get.md)               | issues a `GET` to the specified URL                                                                                |
| [`hx-post`](@/attributes/hx-post.md)             | issues a `POST` to the specified URL                                                                               |
| [`hx-on*`](@/attributes/hx-on.md)                | handle events with inline scripts on elements                                                                      |
| [`hx-push-url`](@/attributes/hx-push-url.md)     | push a URL into the browser location bar to create history                                                         |
| [`hx-select`](@/attributes/hx-select.md)         | select content to swap in from a response                                                                          |
| [`hx-select-oob`](@/attributes/hx-select-oob.md) | select content to swap in from a response, somewhere other than the target (out of band)                           |
| [`hx-swap`](@/attributes/hx-swap.md)             | controls how content will swap in (`outerHTML`, `beforeend`, `afterend`, ...)                                      |
| [`hx-swap-oob`](@/attributes/hx-swap-oob.md)     | mark element to swap in from a response (out of band)                                                              |
| [`hx-target`](@/attributes/hx-target.md)         | specifies the target element to be swapped                                                                         |
| [`hx-trigger`](@/attributes/hx-trigger.md)       | specifies the event that triggers the request                                                                      |
| [`hx-vals`](@/attributes/hx-vals.md)             | add values to submit with the request (JSON format)                                                                |

</div>

## Additional Attribute Reference {#attributes-additional}

All other attributes available in htmx.

<div class="info-table">

| Attribute                                            | Description                                                                                                                        |
|------------------------------------------------------|------------------------------------------------------------------------------------------------------------------------------------|
| [`hx-boost`](@/attributes/hx-boost.md)               | add [progressive enhancement](https://en.wikipedia.org/wiki/Progressive_enhancement) for links and forms                           |
| [`hx-confirm`](@/attributes/hx-confirm.md)           | shows a `confirm()` dialog before issuing a request                                                                                |
| [`hx-delete`](@/attributes/hx-delete.md)             | issues a `DELETE` to the specified URL                                                                                             |
| [`hx-disable`](@/attributes/hx-disable.md)           | disables htmx processing for the given node and any children nodes                                                                 |
| [`hx-disabled-elt`](@/attributes/hx-disabled-elt.md) | adds the `disabled` attribute to the specified elements while a request is in flight                                               |
| [`hx-disinherit`](@/attributes/hx-disinherit.md)     | control and disable automatic attribute inheritance for child nodes                                                                |
| [`hx-encoding`](@/attributes/hx-encoding.md)         | changes the request encoding type                                                                                                  |
| [`hx-ext`](@/attributes/hx-ext.md)                   | extensions to use for this element                                                                                                 |
| [`hx-headers`](@/attributes/hx-headers.md)           | adds to the headers that will be submitted with the request                                                                        |
| [`hx-history`](@/attributes/hx-history.md)           | prevent sensitive data being saved to the history cache                                                                            |
| [`hx-history-elt`](@/attributes/hx-history-elt.md)   | the element to snapshot and restore during history navigation                                                                      |
| [`hx-include`](@/attributes/hx-include.md)           | include additional data in requests                                                                                                |
| [`hx-indicator`](@/attributes/hx-indicator.md)       | the element to put the `htmx-request` class on during the request                                                                  |
| [`hx-inherit`](@/attributes/hx-inherit.md)           | control and enable automatic attribute inheritance for child nodes if it has been disabled by default                            |
| [`hx-params`](@/attributes/hx-params.md)             | filters the parameters that will be submitted with a request                                                                       |
| [`hx-patch`](@/attributes/hx-patch.md)               | issues a `PATCH` to the specified URL                                                                                              |
| [`hx-preserve`](@/attributes/hx-preserve.md)         | specifies elements to keep unchanged between requests                                                                              |
| [`hx-prompt`](@/attributes/hx-prompt.md)             | shows a `prompt()` before submitting a request                                                                                     |
| [`hx-put`](@/attributes/hx-put.md)                   | issues a `PUT` to the specified URL                                                                                                |
| [`hx-replace-url`](@/attributes/hx-replace-url.md)   | replace the URL in the browser location bar                                                                                        |
| [`hx-request`](@/attributes/hx-request.md)           | configures various aspects of the request                                                                                          |
| [`hx-sync`](@/attributes/hx-sync.md)                 | control how requests made by different elements are synchronized                                                                   |
| [`hx-validate`](@/attributes/hx-validate.md)         | force elements to validate themselves before a request                                                                             |
| [`hx-vars`](@/attributes/hx-vars.md)                 | adds values dynamically to the parameters to submit with the request (deprecated, please use [`hx-vals`](@/attributes/hx-vals.md)) |

</div>

## CSS Class Reference {#classes}

<div class="info-table">

| Class | Description |
|-----------|-------------|
| `htmx-added` | Applied to a new piece of content before it is swapped, removed after it is settled.
| `htmx-indicator` | A dynamically generated class that will toggle visible (opacity:1) when a `htmx-request` class is present
| `htmx-request` | Applied to either the element or the element specified with [`hx-indicator`](@/attributes/hx-indicator.md) while a request is ongoing
| `htmx-settling` | Applied to a target after content is swapped, removed after it is settled. The duration can be modified via [`hx-swap`](@/attributes/hx-swap.md).
| `htmx-swapping` | Applied to a target before any content is swapped, removed after it is swapped. The duration can be modified via [`hx-swap`](@/attributes/hx-swap.md).

</div>

## HTTP Header Reference {#headers}

### Request Headers Reference {#request_headers}

<div class="info-table">

| Header | Description |
|--------|-------------|
| `HX-Boosted` | indicates that the request is via an element using [hx-boost](@/attributes/hx-boost.md)
| `HX-Current-URL` | the current URL of the browser
| `HX-History-Restore-Request` | "true" if the request is for history restoration after a miss in the local history cache
| `HX-Prompt` | the user response to an [hx-prompt](@/attributes/hx-prompt.md)
| `HX-Request` | always "true"
| `HX-Target` | the `id` of the target element if it exists
| `HX-Trigger-Name` | the `name` of the triggered element if it exists
| `HX-Trigger` | the `id` of the triggered element if it exists

</div>

### Response Headers Reference {#response_headers}

<div class="info-table">

| Header                                               | Description |
|------------------------------------------------------|-------------|
| [`HX-Location`](@/headers/hx-location.md)            | allows you to do a client-side redirect that does not do a full page reload
| [`HX-Push-Url`](@/headers/hx-push-url.md)            | pushes a new url into the history stack
| [`HX-Redirect`](@/headers/hx-redirect.md)            | can be used to do a client-side redirect to a new location
| `HX-Refresh`                                         | if set to "true" the client-side will do a full refresh of the page
| [`HX-Replace-Url`](@/headers/hx-replace-url.md)      | replaces the current URL in the location bar
| `HX-Reswap`                                          | allows you to specify how the response will be swapped. See [hx-swap](@/attributes/hx-swap.md) for possible values
| `HX-Retarget`                                        | a CSS selector that updates the target of the content update to a different element on the page
| `HX-Reselect`                                        | a CSS selector that allows you to choose which part of the response is used to be swapped in. Overrides an existing [`hx-select`](@/attributes/hx-select.md) on the triggering element
| [`HX-Trigger`](@/headers/hx-trigger.md)              | allows you to trigger client-side events
| [`HX-Trigger-After-Settle`](@/headers/hx-trigger.md) | allows you to trigger client-side events after the settle step
| [`HX-Trigger-After-Swap`](@/headers/hx-trigger.md)   | allows you to trigger client-side events after the swap step

</div>

## Event Reference {#events}

<div class="info-table">

| Event | Description |
|-------|-------------|
| [`htmx:abort`](@/events.md#htmx:abort) | send this event to an element to abort a request
| [`htmx:afterOnLoad`](@/events.md#htmx:afterOnLoad) | triggered after an AJAX request has completed processing a successful response
| [`htmx:afterProcessNode`](@/events.md#htmx:afterProcessNode) | triggered after htmx has initialized a node
| [`htmx:afterRequest`](@/events.md#htmx:afterRequest)  | triggered after an AJAX request has completed
| [`htmx:afterSettle`](@/events.md#htmx:afterSettle)  | triggered after the DOM has settled
| [`htmx:afterSwap`](@/events.md#htmx:afterSwap)  | triggered after new content has been swapped in
| [`htmx:beforeCleanupElement`](@/events.md#htmx:beforeCleanupElement)  | triggered before htmx [disables](@/attributes/hx-disable.md) an element or removes it from the DOM
| [`htmx:beforeOnLoad`](@/events.md#htmx:beforeOnLoad)  | triggered before any response processing occurs
| [`htmx:beforeProcessNode`](@/events.md#htmx:beforeProcessNode) | triggered before htmx initializes a node
| [`htmx:beforeRequest`](@/events.md#htmx:beforeRequest)  | triggered before an AJAX request is made
| [`htmx:beforeSwap`](@/events.md#htmx:beforeSwap)  | triggered before a swap is done, allows you to configure the swap
| [`htmx:beforeSend`](@/events.md#htmx:beforeSend)  | triggered just before an ajax request is sent
| [`htmx:beforeTransition`](@/events.md#htmx:beforeTransition)  | triggered before the [View Transition](https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API) wrapped swap occurs
| [`htmx:configRequest`](@/events.md#htmx:configRequest)  | triggered before the request, allows you to customize parameters, headers
| [`htmx:confirm`](@/events.md#htmx:confirm)  | triggered after a trigger occurs on an element, allows you to cancel (or delay) issuing the AJAX request
| [`htmx:historyCacheError`](@/events.md#htmx:historyCacheError)  | triggered on an error during cache writing
| [`htmx:historyCacheMiss`](@/events.md#htmx:historyCacheMiss)  | triggered on a cache miss in the history subsystem
| [`htmx:historyCacheMissError`](@/events.md#htmx:historyCacheMissError)  | triggered on a unsuccessful remote retrieval
| [`htmx:historyCacheMissLoad`](@/events.md#htmx:historyCacheMissLoad)  | triggered on a successful remote retrieval
| [`htmx:historyRestore`](@/events.md#htmx:historyRestore)  | triggered when htmx handles a history restoration action
| [`htmx:beforeHistorySave`](@/events.md#htmx:beforeHistorySave)  | triggered before content is saved to the history cache
| [`htmx:load`](@/events.md#htmx:load)  | triggered when new content is added to the DOM
| [`htmx:noSSESourceError`](@/events.md#htmx:noSSESourceError)  | triggered when an element refers to a SSE event in its trigger, but no parent SSE source has been defined
| [`htmx:onLoadError`](@/events.md#htmx:onLoadError)  | triggered when an exception occurs during the onLoad handling in htmx
| [`htmx:oobAfterSwap`](@/events.md#htmx:oobAfterSwap)  | triggered after an out of band element as been swapped in
| [`htmx:oobBeforeSwap`](@/events.md#htmx:oobBeforeSwap)  | triggered before an out of band element swap is done, allows you to configure the swap
| [`htmx:oobErrorNoTarget`](@/events.md#htmx:oobErrorNoTarget)  | triggered when an out of band element does not have a matching ID in the current DOM
| [`htmx:prompt`](@/events.md#htmx:prompt)  | triggered after a prompt is shown
| [`htmx:pushedIntoHistory`](@/events.md#htmx:pushedIntoHistory)  | triggered after an url is pushed into history
| [`htmx:responseError`](@/events.md#htmx:responseError)  | triggered when an HTTP response error (non-`200` or `300` response code) occurs
| [`htmx:sendAbort`](@/events.md#htmx:sendAbort)  | triggered when a request is aborted
| [`htmx:sendError`](@/events.md#htmx:sendError)  | triggered when a network error prevents an HTTP request from happening
| [`htmx:sseError`](@/events.md#htmx:sseError)  | triggered when an error occurs with a SSE source
| [`htmx:sseOpen`](/events#htmx:sseOpen)  | triggered when a SSE source is opened
| [`htmx:swapError`](@/events.md#htmx:swapError)  | triggered when an error occurs during the swap phase
| [`htmx:targetError`](@/events.md#htmx:targetError)  | triggered when an invalid target is specified
| [`htmx:timeout`](@/events.md#htmx:timeout)  | triggered when a request timeout occurs
| [`htmx:validation:validate`](@/events.md#htmx:validation:validate)  | triggered before an element is validated
| [`htmx:validation:failed`](@/events.md#htmx:validation:failed)  | triggered when an element fails validation
| [`htmx:validation:halted`](@/events.md#htmx:validation:halted)  | triggered when a request is halted due to validation errors
| [`htmx:xhr:abort`](@/events.md#htmx:xhr:abort)  | triggered when an ajax request aborts
| [`htmx:xhr:loadend`](@/events.md#htmx:xhr:loadend)  | triggered when an ajax request ends
| [`htmx:xhr:loadstart`](@/events.md#htmx:xhr:loadstart)  | triggered when an ajax request starts
| [`htmx:xhr:progress`](@/events.md#htmx:xhr:progress)  | triggered periodically during an ajax request that supports progress events

</div>

## JavaScript API Reference {#api}

<div class="info-table">

| Method | Description |
|-------|-------------|
| [`htmx.addClass()`](@/api.md#addClass)  | Adds a class to the given element
| [`htmx.ajax()`](@/api.md#ajax)  | Issues an htmx-style ajax request
| [`htmx.closest()`](@/api.md#closest)  | Finds the closest parent to the given element matching the selector
| [`htmx.config`](@/api.md#config)  | A property that holds the current htmx config object
| [`htmx.createEventSource`](@/api.md#createEventSource)  | A property holding the function to create SSE EventSource objects for htmx
| [`htmx.createWebSocket`](@/api.md#createWebSocket)  | A property holding the function to create WebSocket objects for htmx
| [`htmx.defineExtension()`](@/api.md#defineExtension)  | Defines an htmx [extension](https://htmx.org/extensions)
| [`htmx.find()`](@/api.md#find)  | Finds a single element matching the selector
| [`htmx.findAll()` `htmx.findAll(elt, selector)`](@/api.md#find)  | Finds all elements matching a given selector
| [`htmx.logAll()`](@/api.md#logAll)  | Installs a logger that will log all htmx events
| [`htmx.logger`](@/api.md#logger)  | A property set to the current logger (default is `null`)
| [`htmx.off()`](@/api.md#off)  | Removes an event listener from the given element
| [`htmx.on()`](@/api.md#on)  | Creates an event listener on the given element, returning it
| [`htmx.onLoad()`](@/api.md#onLoad)  | Adds a callback handler for the `htmx:load` event
| [`htmx.parseInterval()`](@/api.md#parseInterval)  | Parses an interval declaration into a millisecond value
| [`htmx.process()`](@/api.md#process)  | Processes the given element and its children, hooking up any htmx behavior
| [`htmx.remove()`](@/api.md#remove)  | Removes the given element
| [`htmx.removeClass()`](@/api.md#removeClass)  | Removes a class from the given element
| [`htmx.removeExtension()`](@/api.md#removeExtension)  | Removes an htmx [extension](https://htmx.org/extensions)
| [`htmx.swap()`](@/api.md#swap)  | Performs swapping (and settling) of HTML content
| [`htmx.takeClass()`](@/api.md#takeClass)  | Takes a class from other elements for the given element
| [`htmx.toggleClass()`](@/api.md#toggleClass)  | Toggles a class from the given element
| [`htmx.trigger()`](@/api.md#trigger)  | Triggers an event on an element
| [`htmx.values()`](@/api.md#values)  | Returns the input values associated with the given element

</div>


## Configuration Reference {#config}

Htmx has some configuration options that can be accessed either programmatically or declaratively.  They are
listed below:

<div class="info-table">

| Config Variable                       | Info                                                                                                                                                                       |
|---------------------------------------|----------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `htmx.config.historyEnabled`          | defaults to `true`, really only useful for testing                                                                                                                         |
| `htmx.config.historyCacheSize`        | defaults to 10                                                                                                                                                             |
| `htmx.config.refreshOnHistoryMiss`    | defaults to `false`, if set to `true` htmx will issue a full page refresh on history misses rather than use an AJAX request                                                |
| `htmx.config.defaultSwapStyle`        | defaults to `innerHTML`                                                                                                                                                    |
| `htmx.config.defaultSwapDelay`        | defaults to 0                                                                                                                                                              |
| `htmx.config.defaultSettleDelay`      | defaults to 20                                                                                                                                                             |
| `htmx.config.includeIndicatorStyles`  | defaults to `true` (determines if the indicator styles are loaded)                                                                                                         |
| `htmx.config.indicatorClass`          | defaults to `htmx-indicator`                                                                                                                                               |
| `htmx.config.requestClass`            | defaults to `htmx-request`                                                                                                                                                 |
| `htmx.config.addedClass`              | defaults to `htmx-added`                                                                                                                                                   |
| `htmx.config.settlingClass`           | defaults to `htmx-settling`                                                                                                                                                |
| `htmx.config.swappingClass`           | defaults to `htmx-swapping`                                                                                                                                                |
| `htmx.config.allowEval`               | defaults to `true`, can be used to disable htmx's use of eval for certain features (e.g. trigger filters)                                                                  |
| `htmx.config.allowScriptTags`         | defaults to `true`, determines if htmx will process script tags found in new content                                                                                       |
| `htmx.config.inlineScriptNonce`       | defaults to `''`, meaning that no nonce will be added to inline scripts                                                                                                    |
| `htmx.config.inlineStyleNonce`        | defaults to `''`, meaning that no nonce will be added to inline styles                                                                                                     |
| `htmx.config.attributesToSettle`      | defaults to `["class", "style", "width", "height"]`, the attributes to settle during the settling phase                                                                    |
| `htmx.config.wsReconnectDelay`        | defaults to `full-jitter`                                                                                                                                                  |
| `htmx.config.wsBinaryType`            | defaults to `blob`, the [the type of binary data](https://developer.mozilla.org/docs/Web/API/WebSocket/binaryType) being received over the WebSocket connection            |
| `htmx.config.disableSelector`         | defaults to `[hx-disable], [data-hx-disable]`, htmx will not process elements with this attribute on it or a parent                                                        |
| `htmx.config.disableInheritance`      | defaults to `false`. If it is set to `true`, the inheritance of attributes is completely disabled and you can explicitly specify the inheritance with the [hx-inherit](@/attributes/hx-inherit.md) attribute.
| `htmx.config.withCredentials`         | defaults to `false`, allow cross-site Access-Control requests using credentials such as cookies, authorization headers or TLS client certificates                          |
| `htmx.config.timeout`                 | defaults to 0, the number of milliseconds a request can take before automatically being terminated                                                                         |
| `htmx.config.scrollBehavior`          | defaults to 'instant', the scroll behavior when using the [show](@/attributes/hx-swap.md#scrolling-scroll-show) modifier with `hx-swap`. The allowed values are `instant` (scrolling should happen instantly in a single jump), `smooth` (scrolling should animate smoothly) and `auto` (scroll behavior is determined by the computed value of [scroll-behavior](https://developer.mozilla.org/en-US/docs/Web/CSS/scroll-behavior)). |
| `htmx.config.defaultFocusScroll`      | if the focused element should be scrolled into view, defaults to false and can be overridden using the [focus-scroll](@/attributes/hx-swap.md#focus-scroll) swap modifier. |
| `htmx.config.getCacheBusterParam`     | defaults to false, if set to true htmx will append the target element to the `GET` request in the format `org.htmx.cache-buster=targetElementId`                           |
| `htmx.config.globalViewTransitions`   | if set to `true`, htmx will use the [View Transition](https://developer.mozilla.org/en-US/docs/Web/API/View_Transitions_API) API when swapping in new content.             |
| `htmx.config.methodsThatUseUrlParams` | defaults to `["get", "delete"]`, htmx will format requests with these methods by encoding their parameters in the URL, not the request body                                |
| `htmx.config.selfRequestsOnly`        | defaults to `true`, whether to only allow AJAX requests to the same domain as the current document                                                             |
| `htmx.config.ignoreTitle`             | defaults to `false`, if set to `true` htmx will not update the title of the document when a `title` tag is found in new content                                            |
| `htmx.config.scrollIntoViewOnBoost`   | defaults to `true`, whether or not the target of a boosted element is scrolled into the viewport. If `hx-target` is omitted on a boosted element, the target defaults to `body`, causing the page to scroll to the top. |
| `htmx.config.triggerSpecsCache`       | defaults to `null`, the cache to store evaluated trigger specifications into, improving parsing performance at the cost of more memory usage. You may define a simple object to use a never-clearing cache, or implement your own system using a [proxy object](https://developer.mozilla.org/docs/Web/JavaScript/Reference/Global_Objects/Proxy) |
| `htmx.config.responseHandling`        | the default [Response Handling](@/docs.md#response-handling) behavior for response status codes can be configured here to either swap or error                             |
| `htmx.config.allowNestedOobSwaps`     | defaults to `true`, whether to process OOB swaps on elements that are nested within the main response element. See [Nested OOB Swaps](@/attributes/hx-swap-oob.md#nested-oob-swaps). |

</div>

You can set them directly in javascript, or you can use a `meta` tag:

``` html {.line-numbers}
<meta name="htmx-config" content='{"defaultSwapStyle":"outerHTML"}'>
```



# 🌘 CSS Scope Inline

A JS library which allow `me` to be used in CSS selectors, by using a `MutationObserver` to monitor the DOM

![cover](https://github.com/gnat/css-scope-inline/assets/24665/c4935c1b-34e3-4220-9d42-11f064999a57)
(Art by [shahabalizadeh](https://www.artstation.com/artwork/zDgdd))

## Why does this exist?

* You want an easy inline vanilla CSS experience without Tailwind CSS.
* Hate creating unique class names over.. and over.. to use once.
* You want to co-locate your styles for ⚡️ [Locality of Behavior (LoB)](https://htmx.org/essays/locality-of-behaviour/)
* You wish `this` would work in `<style>` tags.
* Want all CSS features: [Nesting](https://caniuse.com/css-nesting), animations. Get scoped [`@keyframes`](https://github.com/gnat/css-scope-inline/blob/main/example.html#L50)!
* You wish `@media` queries were shorter for [responsive design](https://tailwindcss.com/docs/responsive-design).
* Only 16 lines. No build step. No dependencies.
* Pairs well with [htmx](https://htmx.org) and [Surreal](https://github.com/gnat/surreal)
* Want fewer layers, less complexity. Are aware of the cargo cult. ✈️

✨ Want to also scope your `<script>` tags? See our companion project [Surreal](https://github.com/gnat/surreal)

## 👁️ How does it look?
``` html {.line-numbers}
<div>
    <style>
        me { background: red; } /* ✨ this & self also work! */
        me button { background: blue; } /* style child elements inline! */
    </style>
    <button>I'm blue</button>
</div>
```
See the [Live Example](https://gnat.github.io/css-scope-inline/example.html)! Then [view source](https://github.com/gnat/css-scope-inline/blob/main/example.html).

## 🌘 How does it work?

This uses `MutationObserver` to monitor the DOM, and the moment a `<style>` tag is seen, it scopes the styles to whatever the parent element is. No flashing or popping. 

This method also leaves your existing styles untouched, allowing you to mix and match at your leisure.

## 🎁 Install

✂️ copy + 📋 paste the snippet into `<script>` in your `<head>`

Or, [📥 download](https://raw.githubusercontent.com/gnat/css-scope-inline/main/script.js) into your project, and add `<script src="script.js"></script>` in your `<head>`

Or, 🌐 CDN: `<script src="https://cdn.jsdelivr.net/gh/gnat/css-scope-inline@main/script.js"></script>`

## 🤔 Why consider this over Tailwind CSS?

Use whatever you'd like, but there's a few advantages with this approach over Tailwind, Twind, UnoCSS:

* No [repeated styles](https://tailwindcss.com/docs/reusing-styles) on child elements (..no [@apply](https://tailwindcss.com/docs/reusing-styles#extracting-classes-with-apply), no `[&>thing]` on each style).
* No repeated prefixes for media queries, hover, focus, etc.
* No visual noise on every `<div>`. Use a local `<style>` per group.
* Share syntax between local and external styles. It's just CSS.
* Regain your "inspect, play with styles, paste" workflow in your web browser!
* No suffering from lost syntax highlighting on properties and units.
* No high risk of eventually requiring a build step.
* No chance of [deprecations](https://windicss.org/posts/sunsetting.html). 16 lines is infinitely maintainable.
* No suffering from FOUC (a flash of unstyled content).
* Zero friction movement of styles between inline and `.css` files. Just replace `me`
* No special tooling or plugins to install.

## ⚡ Workflow Tips

* Flat, 1 selector per line can be very short like Tailwind. See the examples.
* Use just plain CSS variables in your design system.
* Use the short `@media` queries for responsive design.
  * Mobile First (flow: **above** breakpoint): **🟢 None (xs)** `sm` `md` `lg` `xl` `xx` 🏁
  * Desktop First (flow: **below** breakpoint): 🏁 `xs-` `sm-` `md-` `lg-` `xl-` **🟢 None (xx)**
  * 🟢 = No breakpoint. Default. See the [Live Example](https://gnat.github.io/css-scope-inline/example.html)!
  * Based on [Tailwind](https://tailwindcss.com/docs/responsive-design) breakpoints. We use `xx` not `2xl` to not break CSS highlighters.
  * Unlike Tailwind, you can [nest your @media styles](https://developer.chrome.com/articles/css-nesting/#nesting-media)!
* Positional selectors may be easier using `div[n1]` for `<div n1>` instead of `div:nth-child(1)`
* Try tools like- Auto complete styles: [VSCode](https://code.visualstudio.com/) or [Sublime](https://packagecontrol.io/packages/Emmet)

## 👁️ CSS Scope Inline vs Tailwind CSS Showdowns
### Basics
Tailwind verbosity goes up with more child elements.
``` html {.line-numbers}
<div>
    <style>
        me { background: red; }
        me div { background: green; }
        me [n1] { background: yellow; }
        me [n2] { background: blue; }
    </style>
    red
    <div>green</div>
    <div>green</div>
    <div>green</div>
    <div n1>yellow</div>
    <div n2>blue</div>
    <div>green</div>
    <div>green</div>
</div>

<div class="bg-[red]">
    red
    <div class="bg-[green]">green</div>
    <div class="bg-[green]">green</div>
    <div class="bg-[green]">green</div>
    <div class="bg-[yellow]">yellow</div>
    <div class="bg-[blue]">blue</div>
    <div class="bg-[green]">green</div>
    <div class="bg-[green]">green</div>
</div>
```

### CSS variables and child elements
At first glance, **Tailwind Example 2** looks very promising! Exciting ...but:
* 🔴 **Every child style requires an explicit selector.**
  * Tailwinds' shorthand advantages sadly disappear.
  * Any more child styles added in Tailwind will become longer than vanilla CSS.
  * This limited example is the best case scenario for Tailwind.
* 🔴 Not visible on github: **no highlighting for properties and units** begins to be painful.
``` html {.line-numbers}
<!doctype html>
<html>
    <head>
        <style>
            :root {
                --color-1: hsl(0 0% 88%);
                --color-1-active: hsl(214 20% 70%);
            }
        </style>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/gh/gnat/css-scope-inline@main/script.js"></script>
    </head>
    <body>
        <!-- CSS Scope Inline -->
        <div>
            <style>
               me { margin:8px 6px; }
               me div a { display:block; padding:8px 12px; margin:10px 0; background:var(--color-1); border-radius:10px; text-align:center; }
               me div a:hover { background:var(--color-1-active); color:white; }
            </style>
            <div><a href="#">Home</a></div>
            <div><a href="#">Team</a></div>
            <div><a href="#">Profile</a></div>
            <div><a href="#">Settings</a></div>
            <div><a href="#">Log Out</a></div>
        </div>

        <!-- Tailwind Example 1 -->
        <div class="mx-2 my-4">
            <div><a href="#" class="block py-2 px-3 my-2 bg-[--color-1] rounded-lg text-center hover:bg-[--color-1-active] hover:text-white">Home</a></div>
            <div><a href="#" class="block py-2 px-3 my-2 bg-[--color-1] rounded-lg text-center hover:bg-[--color-1-active] hover:text-white">Team</a></div>
            <div><a href="#" class="block py-2 px-3 my-2 bg-[--color-1] rounded-lg text-center hover:bg-[--color-1-active] hover:text-white">Profile</a></div>
            <div><a href="#" class="block py-2 px-3 my-2 bg-[--color-1] rounded-lg text-center hover:bg-[--color-1-active] hover:text-white">Settings</a></div>
            <div><a href="#" class="block py-2 px-3 my-2 bg-[--color-1] rounded-lg text-center hover:bg-[--color-1-active] hover:text-white">Log Out</a></div>
        </div>

        <!-- Tailwind Example 2 -->
        <div class="mx-2 my-4
            [&_div_a]:block [&_div_a]:py-2 [&_div_a]:px-3 [&_div_a]:my-2 [&_div_a]:bg-[--color-1] [&_div_a]:rounded-lg [&_div_a]:text-center
            [&_div_a:hover]:bg-[--color-1-active] [&_div_a:hover]:text-white">
            <div><a href="#">Home</a></div>
            <div><a href="#">Team</a></div>
            <div><a href="#">Profile</a></div>
            <div><a href="#">Settings</a></div>
            <div><a href="#">Log Out</a></div>
        </div>
    </body>
</html>
```
## 🔎 Technical FAQ
* Why do you use `querySelectorAll()` and not just process the `MutationObserver` results directly?
  * This was indeed the original design; it will work well up until you begin recieving subtrees (ex: DOM swaps with [htmx](https://htmx.org), ajax, jquery, etc.) which requires walking all subtree elements to ensure we do not miss a `<style>`. This unfortunately involves re-scanning thousands of repeated elements. This is why `querySelectorAll()` ends up the performance (and simplicity) winner.
 


# Websockets application

Very brief example of using websockets with HTMX and FastHTML

``` python {.line-numbers}
from asyncio import sleep
from fasthtml.common import *

app = FastHTML(exts='ws')
rt = app.route

def mk_inp(): return Input(id='msg')
nid = 'notifications'

@rt('/')
async def get():
    cts = Div(
        Div(id=nid),
        Form(mk_inp(), id='form', ws_send=True),
        hx_ext='ws', ws_connect='/ws')
    return Titled('Websocket Test', cts)

async def on_connect(send): await send(Div('Hello, you have connected', id=nid))
async def on_disconnect( ): print('Disconnected!')

@app.ws('/ws', conn=on_connect, disconn=on_disconnect)
async def ws(msg:str, send):
    await send(Div('Hello ' + msg, id=nid))
    await sleep(2)
    return Div('Goodbye ' + msg, id=nid), mk_inp()

serve()
```

# Todo list application

Detailed walk-thru of a complete CRUD app in FastHTML showing idiomatic use of FastHTML and HTMX patterns.">###

## Walkthrough of an idiomatic fasthtml app

``` python {.line-numbers} 

# This fasthtml app includes functionality from fastcore, starlette, fastlite, and fasthtml itself.
# Run with: `python adv_app.py`
# Importing from `fasthtml.common` brings the key parts of all of these together.
# For simplicity, you can just `from fasthtml.common import *`:

from fasthtml.common import *

# ...or you can import everything into a namespace:
# from fasthtml import common as fh
# ...or you can import each symbol explicitly (which we're commenting out here but including for completeness):

"""
from fasthtml.common import (
    # These are the HTML components we use in this app
    A, AX, Button, Card, CheckboxX, Container, Div, Form, Grid, Group, H1, H2, Hidden, Input, Li, Main, Script, Style, Textarea, Title, Titled, Ul,
    # These are FastHTML symbols we'll use
    Beforeware, FastHTML, fast_app, SortableJS, fill_form, picolink, serve,
    # These are from Starlette, Fastlite, fastcore, and the Python stdlib
    FileResponse, NotFoundError, RedirectResponse, database, patch, dataclass
)
"""

from hmac import compare_digest

# You can use any database you want; it'll be easier if you pick a lib that supports the MiniDataAPI spec.
# Here we are using SQLite, with the FastLite library, which supports the MiniDataAPI spec.
db = database('data/utodos.db')
# The `t` attribute is the table collection. The `todos` and `users` tables are not created if they don't exist.
# Instead, you can use the `create` method to create them if needed.
todos,users = db.t.todos,db.t.users
if todos not in db.t:
    # You can pass a dict, or kwargs, to most MiniDataAPI methods.
    users.create(dict(name=str, pwd=str), pk='name')
    todos.create(id=int, title=str, done=bool, name=str, details=str, priority=int, pk='id')
# Although you can just use dicts, it can be helpful to have types for your DB objects.
# The `dataclass` method creates that type, and stores it in the object, so it will use it for any returned items.
Todo,User = todos.dataclass(),users.dataclass()

# Any Starlette response class can be returned by a FastHTML route handler.
# In that case, FastHTML won't change it at all.
# Status code 303 is a redirect that can change POST to GET, so it's appropriate for a login page.
login_redir = RedirectResponse('/login', status_code=303)

# The `before` function is a *Beforeware* function. These are functions that run before a route handler is called.
def before(req, sess):
    # This sets the `auth` attribute in the request scope, and gets it from the session.
    # The session is a Starlette session, which is a dict-like object which is cryptographically signed,
    # so it can't be tampered with.
    # The `auth` key in the scope is automatically provided to any handler which requests it, and can not
    # be injected by the user using query params, cookies, etc, so it should be secure to use.
    auth = req.scope['auth'] = sess.get('auth', None)
    # If the session key is not there, it redirects to the login page.
    if not auth: return login_redir
    # `xtra` is part of the MiniDataAPI spec. It adds a filter to queries and DDL statements,
    # to ensure that the user can only see/edit their own todos.
    todos.xtra(name=auth)

markdown_js = """
import { marked } from "https://cdn.jsdelivr.net/npm/marked/lib/marked.esm.js";
proc_htmx('.markdown', e => e.innerHTML = marked.parse(e.textContent));
"""

# We will use this in our `exception_handlers` dict
def _not_found(req, exc): return Titled('Oh no!', Div('We could not find that page :('))

# To create a Beforeware object, we pass the function itself, and optionally a list of regexes to skip.
bware = Beforeware(before, skip=[r'/favicon\.ico', r'/static/.*', r'.*\.css', '/login'])
# The `FastHTML` class is a subclass of `Starlette`, so you can use any parameters that `Starlette` accepts.
# In addition, you can add your Beforeware here, and any headers you want included in HTML responses.
# FastHTML includes the "HTMX" and "Surreal" libraries in headers, unless you pass `default_hdrs=False`.
app = FastHTML(before=bware,
               # These are the same as Starlette exception_handlers, except they also support `FT` results
               exception_handlers={404: _not_found},
               # PicoCSS is a particularly simple CSS framework, with some basic integration built in to FastHTML.
               # `picolink` is pre-defined with the header for the PicoCSS stylesheet.
               # You can use any CSS framework you want, or none at all.
               hdrs=(picolink,
                     # `Style` is an `FT` object, which are 3-element lists consisting of:
                     # (tag_name, children_list, attrs_dict).
                     # FastHTML composes them from trees and auto-converts them to HTML when needed.
                     # You can also use plain HTML strings in handlers and headers,
                     # which will be auto-escaped, unless you use `NotStr(...string...)`.
                     Style(':root { --pico-font-size: 100%; }'),
                     # Have a look at fasthtml/js.py to see how these Javascript libraries are added to FastHTML.
                     # They are only 5-10 lines of code each, and you can add your own too.
                     SortableJS('.sortable'),
                     # MarkdownJS is actually provided as part of FastHTML, but we've included the js code here
                     # so that you can see how it works.
                     Script(markdown_js, type='module'))
                )
# We add `rt` as a shortcut for `app.route`, which is what we'll use to decorate our route handlers.
# When using `app.route` (or this shortcut), the only required argument is the path.
# The name of the decorated function (eg `get`, `post`, etc) is used as the HTTP verb for the handler.
rt = app.route

# For instance, this function handles GET requests to the `/login` path.
@rt("/login")
def get():
    # This creates a form with two input fields, and a submit button.
    # All of these components are `FT` objects. All HTML tags are provided in this form by FastHTML.
    # If you want other custom tags (e.g. `MyTag`), they can be auto-generated by e.g
    # `from fasthtml.components import MyTag`.
    # Alternatively, manually call e.g `ft(tag_name, *children, **attrs)`.
    frm = Form(
        # Tags with a `name` attr will have `name` auto-set to the same as `id` if not provided
        Input(id='name', placeholder='Name'),
        Input(id='pwd', type='password', placeholder='Password'),
        Button('login'),
        action='/login', method='post')
    # If a user visits the URL directly, FastHTML auto-generates a full HTML page.
    # However, if the URL is accessed by HTMX, then one HTML partial is created for each element of the tuple.
    # To avoid this auto-generation of a full page, return a `HTML` object, or a Starlette `Response`.
    # `Titled` returns a tuple of a `Title` with the first arg and a `Container` with the rest.
    # See the comments for `Title` later for details.
    return Titled("Login", frm)

# Handlers are passed whatever information they "request" in the URL, as keyword arguments.
# Dataclasses, dicts, namedtuples, TypedDicts, and custom classes are automatically instantiated
# from form data.
# In this case, the `Login` class is a dataclass, so the handler will be passed `name` and `pwd`.
@dataclass
class Login: name:str; pwd:str

# This handler is called when a POST request is made to the `/login` path.
# The `login` argument is an instance of the `Login` class, which has been auto-instantiated from the form data.
# There are a number of special parameter names, which will be passed useful information about the request:
# `session`: the Starlette session; `request`: the Starlette request; `auth`: the value of `scope['auth']`,
# `htmx`: the HTMX headers, if any; `app`: the FastHTML app object.
# You can also pass any string prefix of `request` or `session`.
@rt("/login")
def post(login:Login, sess):
    if not login.name or not login.pwd: return login_redir
    # Indexing into a MiniDataAPI table queries by primary key, which is `name` here.
    # It returns a dataclass object, if `dataclass()` has been called at some point, or a dict otherwise.
    try: u = users[login.name]
    # If the primary key does not exist, the method raises a `NotFoundError`.
    # Here we use this to just generate a user -- in practice you'd probably to redirect to a signup page.
    except NotFoundError: u = users.insert(login)
    # This compares the passwords using a constant time string comparison
    # https://sqreen.github.io/DevelopersSecurityBestPractices/timing-attack/python
    if not compare_digest(u.pwd.encode("utf-8"), login.pwd.encode("utf-8")): return login_redir
    # Because the session is signed, we can securely add information to it. It's stored in the browser cookies.
    # If you don't pass a secret signing key to `FastHTML`, it will auto-generate one and store it in a file `./sesskey`.
    sess['auth'] = u.name
    return RedirectResponse('/', status_code=303)

# Instead of using `app.route` (or the `rt` shortcut), you can also use `app.get`, `app.post`, etc.
# In this case, the function name is not used to determine the HTTP verb.
@app.get("/logout")
def logout(sess):
    del sess['auth']
    return login_redir

# FastHTML uses Starlette's path syntax, and adds a `static` type which matches standard static file extensions.
# You can define your own regex path specifiers -- for instance this is how `static` is defined in FastHTML
# `reg_re_param("static", "ico|gif|jpg|jpeg|webm|css|js|woff|png|svg|mp4|webp|ttf|otf|eot|woff2|txt|xml|html")`
# In this app, we only actually have one static file, which is `favicon.ico`. But it would also be needed if
# we were referencing images, CSS/JS files, etc.
# Note, this function is unnecessary, as the `fast_app()` call already includes this functionality.
# However, it's included here to show how you can define your own static file handler.
@rt("/{fname:path}.{ext:static}")
def get(fname:str, ext:str): return FileResponse(f'{fname}.{ext}')

# The `patch` decorator, which is defined in `fastcore`, adds a method to an existing class.
# Here we are adding a method to the `Todo` class, which is returned by the `todos` table.
# The `__ft__` method is a special method that FastHTML uses to convert the object into an `FT` object,
# so that it can be composed into an FT tree, and later rendered into HTML.
@patch
def __ft__(self:Todo):
    # Some FastHTML tags have an 'X' suffix, which means they're "extended" in some way.
    # For instance, here `AX` is an extended `A` tag, which takes 3 positional arguments:
    # `(text, hx_get, target_id)`.
    # All underscores in FT attrs are replaced with hyphens, so this will create an `hx-get` attr,
    # which HTMX uses to trigger a GET request.
    # Generally, most of your route handlers in practice (as in this demo app) are likely to be HTMX handlers.
    # For instance, for this demo, we only have two full-page handlers: the '/login' and '/' GET handlers.
    show = AX(self.title, f'/todos/{self.id}', 'current-todo')
    edit = AX('edit',     f'/edit/{self.id}' , 'current-todo')
    dt = '✅ ' if self.done else ''
    # FastHTML provides some shortcuts. For instance, `Hidden` is defined as simply:
    # `return Input(type="hidden", value=value, **kwargs)`
    cts = (dt, show, ' | ', edit, Hidden(id="id", value=self.id), Hidden(id="priority", value="0"))
    # Any FT object can take a list of children as positional args, and a dict of attrs as keyword args.
    return Li(*cts, id=f'todo-{self.id}')

# This is the handler for the main todo list application.
# By including the `auth` parameter, it gets passed the current username, for displaying in the title.
@rt("/")
def get(auth):
    title = f"{auth}'s Todo list"
    top = Grid(H1(title), Div(A('logout', href='/logout'), style='text-align: right'))
    # We don't normally need separate "screens" for adding or editing data. Here for instance,
    # we're using an `hx-post` to add a new todo, which is added to the start of the list (using 'afterbegin').
    new_inp = Input(id="new-title", name="title", placeholder="New Todo")
    add = Form(Group(new_inp, Button("Add")),
               hx_post="/", target_id='todo-list', hx_swap="afterbegin")
    # In the MiniDataAPI spec, treating a table as a callable (i.e with `todos(...)` here) queries the table.
    # Because we called `xtra` in our Beforeware, this queries the todos for the current user only.
    # We can include the todo objects directly as children of the `Form`, because the `Todo` class has `__ft__` defined.
    # This is automatically called by FastHTML to convert the `Todo` objects into `FT` objects when needed.
    # The reason we put the todo list inside a form is so that we can use the 'sortable' js library to reorder them.
    # That library calls the js `end` event when dragging is complete, so our trigger here causes our `/reorder`
    # handler to be called.
    frm = Form(*todos(order_by='priority'),
               id='todo-list', cls='sortable', hx_post="/reorder", hx_trigger="end")
    # We create an empty 'current-todo' Div at the bottom of our page, as a target for the details and editing views.
    card = Card(Ul(frm), header=add, footer=Div(id='current-todo'))
    # PicoCSS uses `<Main class='container'>` page content; `Container` is a tiny function that generates that.
    # A handler can return either a single `FT` object or string, or a tuple of them.
    # In the case of a tuple, the stringified objects are concatenated and returned to the browser.
    # The `Title` tag has a special purpose: it sets the title of the page.
    return Title(title), Container(top, card)

# This is the handler for the reordering of todos.
# It's a POST request, which is used by the 'sortable' js library.
# Because the todo list form created earlier included hidden inputs with the todo IDs,
# they are passed as form data. By using a parameter called (e.g) "id", FastHTML will try to find
# something suitable in the request with this name. In order, it searches as follows:
# path; query; cookies; headers; session keys; form data.
# Although all these are provided in the request as strings, FastHTML will use your parameter's type
# annotation to try to cast the value to the requested type.
# In the case of form data, there can be multiple values with the same key. So in this case,
# the parameter is a list of ints.
@rt("/reorder")
def post(id:list[int]):
    for i,id_ in enumerate(id): todos.update({'priority':i}, id_)
    # HTMX by default replaces the inner HTML of the calling element, which in this case is the todo list form.
    # Therefore, we return the list of todos, now in the correct order, which will be auto-converted to FT for us.
    # In this case, it's not strictly necessary, because sortable.js has already reorder the DOM elements.
    # However, by returning the updated data, we can be assured that there aren't sync issues between the DOM
    # and the server.
    return tuple(todos(order_by='priority'))

# Refactoring components in FastHTML is as simple as creating Python functions.
# The `clr_details` function creates a Div with specific HTMX attributes.
# `hx_swap_oob='innerHTML'` tells HTMX to swap the inner HTML of the target element out-of-band,
# meaning it will update this element regardless of where the HTMX request originated from.
def clr_details(): return Div(hx_swap_oob='innerHTML', id='current-todo')

# This route handler uses a path parameter `{id}` which is automatically parsed and passed as an int.
@rt("/todos/{id}")
def delete(id:int):
    # The `delete` method is part of the MiniDataAPI spec, removing the item with the given primary key.
    todos.delete(id)
    # Returning `clr_details()` ensures the details view is cleared after deletion,
    # leveraging HTMX's out-of-band swap feature.
    # Note that we are not returning *any* FT component that doesn't have an "OOB" swap, so the target element
    # inner HTML is simply deleted. That's why the deleted todo is removed from the list.
    return clr_details()

@rt("/edit/{id}")
def get(id:int):
    # The `hx_put` attribute tells HTMX to send a PUT request when the form is submitted.
    # `target_id` specifies which element will be updated with the server's response.
    res = Form(Group(Input(id="title"), Button("Save")),
        Hidden(id="id"), CheckboxX(id="done", label='Done'),
        Textarea(id="details", name="details", rows=10),
        hx_put="/", target_id=f'todo-{id}', id="edit")
    # `fill_form` populates the form with existing todo data, and returns the result.
    # Indexing into a table (`todos`) queries by primary key, which is `id` here. It also includes
    # `xtra`, so this will only return the id if it belongs to the current user.
    return fill_form(res, todos[id])

@rt("/")
def put(todo: Todo):
    # `update` is part of the MiniDataAPI spec.
    # Note that the updated todo is returned. By returning the updated todo, we can update the list directly.
    # Because we return a tuple with `clr_details()`, the details view is also cleared.
    return todos.update(todo), clr_details()

@rt("/")
def post(todo:Todo):
    # `hx_swap_oob='true'` tells HTMX to perform an out-of-band swap, updating this element wherever it appears.
    # This is used to clear the input field after adding the new todo.
    new_inp =  Input(id="new-title", name="title", placeholder="New Todo", hx_swap_oob='true')
    # `insert` returns the inserted todo, which is appended to the start of the list, because we used
    # `hx_swap='afterbegin'` when creating the todo list form.
    return todos.insert(todo), new_inp

@rt("/todos/{id}")
def get(id:int):
    todo = todos[id]
    # `hx_swap` determines how the update should occur. We use "outerHTML" to replace the entire todo `Li` element.
    btn = Button('delete', hx_delete=f'/todos/{todo.id}',
                 target_id=f'todo-{todo.id}', hx_swap="outerHTML")
    # The "markdown" class is used here because that's the CSS selector we used in the JS earlier.
    # Therefore this will trigger the JS to parse the markdown in the details field.
    # Because `class` is a reserved keyword in Python, we use `cls` instead, which FastHTML auto-converts.
    return Div(H2(todo.title), Div(todo.details, cls="markdown"), btn)

serve()
 