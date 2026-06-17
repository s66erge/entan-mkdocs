# ~/~ begin <<docs/gong-web-app/center-dashboard.md#libs/cdash.py>>[init]

import asyncio
from fasthtml.common import *
from datetime import datetime
import pandas as pd
import libs.utils as utils
import libs.minio as minio
import libs.dbset as dbset
import libs.messages as messages
import libs.states as states

# ~/~ begin <<docs/gong-web-app/center-dashboard.md#dashboard>>[init]

def top_menu(role):
    return Nav(
            Ul(
                Li(A("Admin", href="/admin_page")) if role == "admin" else None,
                Li(A("Dashboard", href="/dashboard")),
                Li(A("Contact", href="/unfinished")),
                Li(A("About", href="/unfinished")),
                Span(style="display: inline-block; width: 100px;"),
                Button("Download PDF", onclick="window.print()"),

            ),
            Button("Logout", hx_post="/logout"),
    )

# @rt('/dashboard')
def dashboard(session, users, planners):
    sessemail = session['auth']
    u = users[sessemail]
    user_planners = planners("user_email = ?", (u.email,))
    user_centers = [(p.center_name) for p in user_planners] 
    select = Select(
        Option("Select a center", value="", selected=True),
        *[Option(name, value=name) for name in user_centers],
        name="center",
        id="planning-db-select",
        required=True
    )
    form = Form(
        select,
        Button("STATUS AND CONFIGURATION", type="submit", onclick="document.getElementById('myForm').action='/status_page'"),
        Button("MODIFY GONG PLANNING", 
               type="submit", onclick="document.getElementById('myForm').action='/planning_page'") if len(user_centers) >= 1 else None,
        action="/default_route",
        id="myForm",
        method="get",
    )
    return Main(
        top_menu(session['role']),
        H1("Dashboard"),
        Div(P(f"You are logged in as '{u.email}' with role '{u.role_name}'"),
            P(f"You are a registered planner for the following center(s): {', '.join(user_centers)}") if len(user_centers) >= 1 else P("You are not a registered planner for any center. Please contact your administrator."),
            utils.toggle_markdown("dhamma-org-and-gong-periods"),
            Br(),
            utils.display_markdown("dashboard"),
            P(A("CONSULT PLANNING", href="/consult_page",
                style="font-size: 24px;")),
            Br(),
            Hr(style="border: none; height: 4px; background-color: deepskyblue;"),
            Br(),
            Div(
                form
            ),
            cls="container"
        ),
        cls="container",
    )
# ~/~ end
# ~/~ begin <<docs/gong-web-app/center-dashboard.md#status-page>>[init]

#@rt('/status_page')
def status_page(session, center_name, centers, users, csms):
    state_mach = csms[center_name]
    #state = state_mach.configuration[0].id
    state_list = states.status_to_stri(state_mach.configuration_values)
    extended_states = states.status_to_stri(state_mach.configuration)
    email = session[utils.Skey.AUTH]
    user_timezone = users[email].timezone
    center_obj = centers[center_name]
    pi_database_date = center_obj.pi_db_date
    config_file = minio.get_excel_minio(center_name)
    params = minio.params_from_excel_minio(center_name)
    ct_timezone = params[utils.Pkey.TIMEZON]
    db_file = utils.get_db_path() + dbset.gong_db_name(center_name)
    db_center = database(db_file)
    gongs_df = pd.DataFrame(db_center.t.gongs())
    targets_df = pd.DataFrame(db_center.t.targets())
    db_center.close()
    replace_df = pd.DataFrame(minio.dicts_from_excel_minio(center_name,"replacement"))
    inside_df = pd.DataFrame(minio.dicts_from_excel_minio(center_name,"inside"))
    html_gongs = gongs_df.fillna("").to_html(index=False)
    html_targets = targets_df.fillna("").to_html(index=False)
    html_replace = replace_df.fillna("").to_html(index=False)
    html_inside = inside_df.fillna("").to_html(index=False)
    return Main(
        top_menu(session['role']),
        Div(utils.display_markdown("planning-free-t" if "free" in state_list else "planning-busy-t")),
        H1(f"{center_name}"),
        P(f"Current center state: {extended_states.replace(",", " , ")}"),
        P(f"Center timezone: {ct_timezone}, local center time now: {utils.short_iso(datetime.now() , ct_timezone)}", Br(),
          f"Your browser timezone: {user_timezone}, your time now: {utils.short_iso(datetime.now(), user_timezone)}", Br(),
          f"UTC time now: {utils.short_iso(datetime.now())}",Br(),Br(),
          f"Local database in center was installed on: {pi_database_date}",
          f"Last result: {state_mach.model.last_result}" if state_mach.model.last_result else None
        ),
        H3("Center gongs and targets"),
        utils.toggle_markdown("gongs-and-targets"), Br(),
        Safe(html_gongs),
        Safe(html_targets),
        P(f"Default gong id for copied periods: {params[utils.Pkey.GONG_ID]}", Br(),
          f"Default target(s) for copied periods: {params[utils.Pkey.TARGETS]}"),
        H3("Configuration"),
        Div(H4("dhamma.org period types replacement table"),
            utils.toggle_markdown("period-type-replacement"), Br(),
            Safe(html_replace)) if len(replace_df) > 0 else P("No data in the 'replacement' table"),
        Div(H4("gong planning instructions for dhamma.org periods overlaps/gaps"),
            utils.toggle_markdown("period-type-replacement"), Br(),
            Safe(html_inside)) if len(inside_df) > 0 else P("No data in the 'overlap/gaps' table"),
        P(f"Parameters: {params}"),
        H3("Center states history"),
        Ul(*[Li(item) for item in csms[center_name].active_listeners[0].entries[::-1]]),
        Div(
            H4("Download the center configuration or database (see the production date above)"),
            Span(
                Button("Download Excel configuration", 
                    onclick=f"window.open('/download_file/?filepath={config_file}', '_blank'); return false;",
                    hx_no_process="true", hx_boost="false"),
                Span(style="display: inline-block; width: 20px;"),
                Button("Download database", 
                    onclick=f"window.open('/download_file/?filepath={db_file}', '_blank'); return false;",
                    hx_no_process="true", hx_boost="false")
            ),
            Br(),Br(),
            H4("Upload the center excel configuration"),
            Div(messages.feedback_to_user(params), id="config-feedback"),
            Form(hx_post="upload_config", hx_target="#config-feedback",
                hx_confirm="Are you ABSOLUTELY sure to change this center configuration?")
                (Input(type="hidden", name="center_name", value=center_name),
                 Input(type="file", name="file"),
                 Button("Upload", type="submit"),
            ),
            Br(),Br(),
            A("set FREE",href="/planning/abandon_edit") 
        ) if session[utils.Skey.ROLE] == "admin" else None,
        cls="container"
    )

async def upload_config(file: UploadFile, center_name: str):
    if file.filename != f"{center_name}.xlsx":
        mess = {"error": "bad_config_filename"}
    elif center_name != "all_centers" and states.csms[center_name].configuration[0].id != "free":
        mess = {"error": "center_not_free"}
    else:
        try:
            filebuffer = await file.read()
            upload_dir = Path(utils.get_db_path())
            (upload_dir / file.filename).write_bytes(filebuffer)
            await asyncio.to_thread(minio.save_excel_minio, center_name)
            mess = {"success": "config_uploaded"}
        except Exception as e:
            return Redirect(f'/db_error?etext={e}')
    return Div(messages.feedback_to_user(mess))

# ~/~ end
# ~/~ end
