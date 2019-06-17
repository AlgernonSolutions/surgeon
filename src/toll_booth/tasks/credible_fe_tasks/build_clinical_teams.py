from aws_xray_sdk.core import xray_recorder


# @xray_recorder.capture('build_clinical_teams')
def build_clinical_teams(**kwargs):
    from toll_booth.obj import StaticJson

    id_source = kwargs['id_source']
    team_json = StaticJson.for_team_data(id_source)
    teams = team_json['teams']
    manual_assignments = team_json['manual_assignments']
    first_level = team_json['first_level']
    default_team = team_json['default_team']
    emp_data = kwargs['emp_data']

    for entry in emp_data:
        int_emp_id = int(entry['Employee ID'])
        str_emp_id = str(int_emp_id)
        supervisor_names = entry['Supervisors']
        profile_code = entry['profile_code']
        if supervisor_names is None or profile_code != 'CSA Community Support Worker NonLicensed':
            continue
        emp_record = {
            'emp_id': int_emp_id,
            'first_name': entry['First Name'],
            'last_name': entry['Last Name'],
            'profile_code': entry['profile_code'],
            'caseload': []
        }
        if str_emp_id in manual_assignments:
            teams[manual_assignments[str_emp_id]].append(emp_record)
            continue
        for name in first_level:
            if name in supervisor_names:
                teams[name].append(emp_record)
                break
        else:
            teams[default_team].append(emp_record)
    return {'teams': teams}
