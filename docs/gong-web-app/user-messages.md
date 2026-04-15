# Messages to the user

```python
#| file: libs/messages.py 

from fasthtml.common import *

<<feedback-to-user>>
```

### Success/error message

```python
#| id: feedback-to-user

def feed_text(params):
    # query_params = dict(request.query_params)
    # Handle success and error messages
    success_messages = {
        'login_code_sent': "A code to sign in has been sent to your email. Please check your inbox and enter the code here below. The code will expire in 15 minutes.",
        'user_added': 'User added successfully!',
        'center_added': 'Center added successfully!',
        'planner_added': 'Planner association adSded successfully!',
        'user_deleted': 'User deleted successfully!',
        'center_deleted': 'Center and associated database deleted successfully!',
        'planner_deleted': 'Planner association deleted successfully!',
        'new_course': 'New line added if did not exist already. Please review the plan and submit changes to update the center gong.',
        'line_deleted': 'Line deleted. Please review the plan and submit changes to update the center gong.',
        'show_plan': 'Here is the plan you already worked on.',
        'config_uploaded': "New configuration loaded in database",
        'config_downloaded': "Configuration in database downloaded",
        'time_deleted': f'Gong playing time deleted: {params.get("time", "")}.',
        'time_inserted': f'Gong playing time inserted: {params.get("time", "")}.',
        'time_modified': f'Gong playing time modified: {params.get("time", "")}.',
        'time_duplicated': f'New time for gong planning: {params.get("time", "")}.'
    }
    error_messages = {
        'missing_email':'Email is required.',
        'not_registered':f'Email "{params.get("email", "")}" is not registered, try again or send a message to xxx@xxx.xx to get registered',
        'invalid_or_expired_code': 'The code is invalid ot expired. Check if if it is correct. Or refresh the page to ask for another code.',
        'missing_fields': 'Please fill in all required fields.',
        'plan_not_ok': 'Correct the planning errors before saving this plan',
        'user_exists': 'User with this email already exists.',
        'center_exists': 'Center with this name already exists.',
        'planner_exists': 'This planner association already exists.',
        'user_not_found': 'User not found.',
        'center_not_found': 'Center not found.',
        'invalid_role': 'Invalid role selected.',
        'db_error': f'Database error occurred: {params.get("etext", "")}. Please contact the program support.',
        'db_file_exists': 'Database file with this name already exists.',
        'template_not_found': 'Template database (mahi.db) not found.',
        'user_has_planners': f'Cannot delete user. User is still associated with centers: {params.get("centers", "")}. Please remove all planner associations first.',
        'center_has_planners': f'Cannot delete center. Center is still associated with users: {params.get("users", "")}. Please remove all planner associations first.',
        'last_planner_for_center': f'Cannot delete planner. This is the last planner for center: "{params.get("center", "")}". Each center must have at least one planner.',
        'bad_config_filename': 'The filename does not match the center name and/or is nor a .xslx excel file',
        'center_not_free': 'Cannot delete a center or modify its config when not in the "free" state: its planning is currently under modification',
        'template_not_free': 'Cannot copy a template if it is not free: being modified',
        'time_already_exists': f'Time already exists in the planning: {params.get("time", "")}.'
    }
    message = ""
    result = ""
    if 'success' in params:
        message = success_messages.get(params['success'], 'Operation completed successfully!')
        result = "success"
    elif 'error' in params:
        message = error_messages.get(params['error'], 'An error occurred.')
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
```
