def all_fields_required_error(form):
    error_msg = "The following fields are required: "
    has_errors = False

    missing_fields = []
    for key in form.keys():
        if not form[key]:
            missing_fields.append(key)
            has_errors = True
    if has_errors:
        return error_msg + ", ".join(missing_fields) + "."
    return False
