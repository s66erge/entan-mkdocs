# ~/~ begin <<docs/gong-web-app/user-messages.md#libs/messages.py>>[init]

from fasthtml.common import *

# ~/~ begin <<docs/gong-web-app/user-messages.md#feedback-to-user>>[init]

def feed_text(params):
    # query_params = dict(request.query_params)
    # Handle success and error messages
    success_messages = {
        'center_added': 'Center added successfully!',
        'center_deleted': 'Center and associated database deleted successfully!',
        'config_downloaded': "Configuration in database downloaded",
        'config_uploaded': "New configuration loaded in database",
        'line_deleted': 'Line deleted. Please review the plan and submit changes to update the center gong.',
        'login_code_sent': "A code to sign in has been sent to your email. Please check your inbox and enter the code here below. The code will expire in 15 minutes.",
        'new_course': 'New line added if did not exist already. Please review the plan and submit changes to update the center gong.',
        'periods_OK': 'All periods are OK, you can save changes for this center timings.',
        'planner_added': 'Planner association adSded successfully!',
        'planner_deleted': 'Planner association deleted successfully!',
        'show_plan': 'Here is the plan you already worked on.',
        'time_deleted': f'Gong playing time deleted: {params.get("time", "")}.',
        'time_duplicated': f'New time for gong planning: {params.get("time", "")}.',
        'time_inserted': f'Gong playing time inserted: {params.get("time", "")}.',
        'time_modified': f'Gong playing time modified: {params.get("time", "")}.',
        'user_added': 'User added successfully!',
        'user_deleted': 'User deleted successfully!',
    }
    error_messages = {
        'bad_config_filename': 'The filename does not match the center name and/or is nor a .xslx excel file',
        'center_exists': 'Center with this name already exists.',
        'center_has_planners': f'Cannot delete center. Center is still associated with users: {params.get("users", "")}. Please remove all planner associations first.',
        'center_not_found': 'Center not found.',
        'center_not_free': 'Cannot delete a center or modify its config when not in the "free" state: its planning is currently under modification',
        'day_type_already_exists': 'Cannot create a new day_type when the name already exists',
        'day_type_unchanged' : 'New day_type same as old day_type',
        'db_error': f'Database error occurred: {params.get("etext", "")}. Please contact the program support.',
        'db_file_exists': 'Database file with this name already exists.',
        'delete_last_time': 'Last time cannot be deleted: this day_type is present in the Structure table',
        'invalid_or_expired_code': 'The code is invalid ot expired. Check if if it is correct. Or refresh the page to ask for another code.',
        'invalid_role': 'Invalid role selected.',
        'last_planner_for_center': f'Cannot delete planner. This is the last planner for center: "{params.get("center", "")}". Each center must have at least one planner.',
        'missing_email':'Email is required.',
        'missing_fields': 'Please fill in all required fields.',
        'not_registered': f'Email "{params.get("email", "")}" is not registered, try again or send a message to xxx@xxx.xx to get registered',
        'period_already_exists': 'Cannot create a new period when the name already exists',
        'periods_errors': 'Error(s) in period(s) timings: see table "Timing errors". Must be corrected before saving these changes', 
        'plan_not_ok': 'Correct the planning errors before saving this plan: click "Load saved plan" and suppress the red indicators.',
        'plan_not_saved': 'Create an initial plan with "(re)Start planning" before loading a saved plan',
        'planner_exists': 'This planner association already exists.',
        'template_not_found': 'Template database (mahi.db) not found.',
        'template_not_free': 'Cannot copy a template if it is not free: being modified',
        'time_already_exists': f'Time already exists in the planning: {params.get("time", "")}.',
        'timings_not_ok': 'Correct the timings errors before saving this plan: click "Load saved timetables" and suppress all lines in table "Timing errors".',
        'user_exists': 'User with this email already exists.',
        'user_has_planners': f'Cannot delete user. User is still associated with centers: {params.get("centers", "")}. Please remove all planner associations first.',
        'user_not_found': 'User not found.',
    }
    message = ""
    result = ""
    if 'success' in params:
        message = success_messages.get(params['success'], f"Operation completed successfully! ({params['success']})")
        result = "success"
    elif 'error' in params:
        message = error_messages.get(params['error'], f"An error occurred. ({params['error']})")
        result = "error"
    return {"mess": message, "res": result}

def feedback_to_user(params):
    # query_params = dict(request.query_params)
    # Handle success and error messages
    mess_dict = feed_text(params)
    message_div = Div(P(""))
    if mess_dict["res"] == 'success':
        message_div = Div(
            Div(P(mess_dict['mess']), style="color: #daecdaff; background: #187449ff; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #198754; font-weight: 500;")
        )
    elif mess_dict["res"] == 'error':
        message_div = Div(
            Div(P(mess_dict['mess']), style="color: #f8d7da; background: #842029; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #dc3545; font-weight: 500;")
        )
    return message_div
# ~/~ end
# ~/~ end
