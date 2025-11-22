# User feedback

### Success/error messages

```{.python file=libs/feedb.py}
from fasthtml.common import *

<<feedback-to-user>>
```


```{.python #feedback-to-user}

def feed_text(params):
    # query_params = dict(request.query_params)
    # Handle success and error messages
    success_messages = {
        'magic_link_sent': "A link to sign in has been sent to your email. Please check your inbox. The link will expire in 15 minutes.",
        'user_added': 'User added successfully!',
        'center_added': 'Center added successfully!',
        'planner_added': 'Planner association added successfully!',
        'user_deleted': 'User deleted successfully!',
        'center_deleted': 'Center and associated database deleted successfully!',
        'planner_deleted': 'Planner association deleted successfully!'
    }
    error_messages = {
        'missing_email':'Email is required.',
        'not_registered':f'Email "{params.get("email", "")}" is not registered, try again or send a message to xxx@xxx.xx to get registered',
        'missing_fields': 'Please fill in all required fields.',
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
        'last_planner_for_center': f'Cannot delete planner. This is the last planner for center: "{params.get("center", "")}". Each center must have at least one planner.'
    }
    message = "Unknown message: please contact the program support"
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
    message_div = Div(P("Unknown message: please contact the program support"))
    if mess_dict["res"] == 'success':
        message_div = Div(
            Div(P(mess_dict['mess']), style="color: #daecdaff; background: #187449ff; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #198754; font-weight: 500;"),
            Small("To clear this message and/or update the tables, reload the page")
        )
    elif mess_dict["res"] == 'error':
        message_div = Div(
            Div(P(mess_dict['mess']), style="color: #f8d7da; background: #842029; padding: 10px; border-radius: 5px; margin: 10px 0; border: 1px solid #dc3545; font-weight: 500;"),
            Small("To clear this message, reload the page")
        )
    return message_div
```
