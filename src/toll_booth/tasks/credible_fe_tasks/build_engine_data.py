from aws_xray_sdk.core import xray_recorder


def _build_team_productivity(team_caseload, encounters, unapproved):
    from datetime import datetime, timedelta

    results = []
    twenty_four_hours_ago = datetime.now() - timedelta(hours=24)
    six_days_ago = datetime.now() - timedelta(days=6)
    past_day_encounters = [x for x in encounters if x['transfer_date'] >= twenty_four_hours_ago]
    next_six_days_encounters = [x for x in encounters if all(
        [x['transfer_date'] < twenty_four_hours_ago, x['transfer_date'] >= six_days_ago]
    )]
    for emp_id, employee in team_caseload.items():
        emp_id = int(emp_id)
        emp_past_day_encounters = [x for x in past_day_encounters if x['emp_id'] == emp_id]
        emp_next_six_days_encounters = [x for x in next_six_days_encounters if x['emp_id'] == emp_id]
        emp_red_x = [x for x in unapproved if x['emp_id'] == emp_id and x['red_x']]
        emp_unapproved = [x for x in unapproved if x['emp_id'] == emp_id and not x['red_x']]
        emp_productivity = {
            'csw_id': emp_id,
            'csw_name':  f'{employee["last_name"]}, {employee["first_name"]}',
            'past_one_day':  {
                'total': sum([x['base_rate'] for x in emp_past_day_encounters]),
                'detailed': emp_past_day_encounters
            },
            'past_six_days': {
                'total': sum([x['base_rate'] for x in emp_next_six_days_encounters]),
                'detailed': emp_next_six_days_encounters
            },
            'unapproved': {
                'total': sum([x['base_rate'] for x in emp_unapproved]),
                'detailed': emp_unapproved
            },
            'red_x': {
                'total': sum([x['base_rate'] for x in emp_red_x]),
                'detailed': emp_red_x
            }
        }
        results.append(emp_productivity)
    return results


def _build_expiration_report(caseloads, assessment_data, assessment_lifespan):
    from datetime import datetime, timedelta

    lifespan_delta = timedelta(days=assessment_lifespan)
    inverted = _invert_caseloads(caseloads)
    now = datetime.now()
    max_assessments = {}
    results = {}
    for assessment in assessment_data:
        client_id = str(assessment['client_id'])
        if client_id not in max_assessments:
            max_assessments[client_id] = []
        max_assessments[client_id].append(assessment['rev_timeout'])
    for client_id, assessments in max_assessments.items():
        assignments = inverted.get(client_id, {'team': 'unassigned', 'csw': 'unassigned'})
        team_name, csw_name = assignments['team'], assignments['csw']
        max_assessment_date = max(assessments)
        expiration_date = max_assessment_date + lifespan_delta
        expired = False
        days_left = (expiration_date - now).days
        if expiration_date < now:
            expired = True
            days_left = 0
        if team_name not in results:
            results[team_name] = {}
        if csw_name not in results[team_name]:
            results[team_name][csw_name] = []
        results[team_name][csw_name].append({
            'team_name': team_name,
            'csw_name': csw_name,
            'client_id': client_id,
            'start_date': max_assessment_date,
            'end_date': expiration_date,
            'is_expired': expired,
            'days_left': days_left
        })
    no_assessments = set(inverted.keys()) - set(max_assessments.keys())
    for client_id in no_assessments:
        assignments = inverted.get(client_id, {'team': 'unassigned', 'csw': 'unassigned'})
        team_name, csw_name = assignments['team'], assignments['csw']
        if team_name not in results:
            results[team_name] = {}
        if csw_name not in results[team_name]:
            results[team_name][csw_name] = []
        results[team_name][csw_name].append({
            'team_name': team_name,
            'csw_name': csw_name,
            'client_id': client_id,
            'start_date': None,
            'end_date': None,
            'is_expired': True,
            'days_left': 0
        })
    return results


def _invert_caseloads(caseloads):
    inverted_caseloads = {}
    for team_name, team_caseload in caseloads.items():
        if team_name == 'unassigned':
            for client in team_caseload:
                inverted_caseloads[client['client_id']] = {'team': 'unassigned', 'csw': 'unassigned', 'emp_id': 0}
            continue
        for emp_id, employee in team_caseload.items():
            csw = f'{employee["last_name"]}, {employee["first_name"]}'
            for client in employee['caseload']:
                inverted_caseloads[client['client_id']] = {'team': team_name, 'csw': csw, 'emp_id': emp_id}
    return inverted_caseloads


def _build_unassigned_report(caseloads):
    report = []
    for client in caseloads['unassigned']:
        primary_staff = client.get('primary_staff')
        if primary_staff:
            if isinstance(primary_staff, list):
                primary_staff = ', '.join(primary_staff)
        report.append({
            'client_id': client['client_id'],
            'client_name': f'{client["last_name"]}, {client["first_name"]}',
            'dob': client['dob'],
            'ssn': client['ssn'],
            'assigned_csa': client['team'],
            'primary_staff': primary_staff
        })
    return report


def _build_not_seen_report(caseloads, encounter_data):
    from datetime import datetime
    today = datetime.now()
    results = []
    inverted = _invert_caseloads(caseloads)
    for client_id, assignments in inverted.items():
        team = assignments['team']
        if team == 'unassigned':
            continue
        csw_id = assignments['emp_id']
        csw_name = assignments['csw']
        client_encounters = [
            x for x in encounter_data if int(x['client_id']) == int(client_id) and x['non_billable'] is False]
        if not client_encounters:
            results.append({
                'team': team,
                'csw_name': csw_name,
                'client_id': client_id,
                'last_service_by_csw': '?',
                'last_bill_service': '?',
                '30_60_90_by_csw': '90',
                '30_60_90_by_last_billed': '90'
            })
            continue
        max_encounter_date = max([x['rev_timeout'] for x in client_encounters])
        per_billable = _calculate_thirty_sixty_ninety(today, max_encounter_date)
        csw_encounters = [x for x in client_encounters if int(x['emp_id']) == int(csw_id)]
        if not csw_encounters:
            results.append({
                'team': team,
                'csw_name': csw_name,
                'client_id': client_id,
                'last_service_by_csw': '?',
                'last_bill_service': max_encounter_date,
                '30_60_90_by_csw': '90',
                '30_60_90_by_last_billed': per_billable
            })
            continue
        max_csw_date = max([x['rev_timeout'] for x in csw_encounters])
        per_csw = _calculate_thirty_sixty_ninety(today, max_csw_date)
        results.append({
            'team': team,
            'csw_name': csw_name,
            'client_id': client_id,
            'last_service_by_csw': max_csw_date,
            'last_bill_service': max_encounter_date,
            '30_60_90_by_csw': per_csw,
            '30_60_90_by_last_billed': per_billable
        })
    return results


def _calculate_thirty_sixty_ninety(today, max_encounter_date):
    encounter_age = (today - max_encounter_date).days
    if encounter_age <= 30:
        return '30'
    if encounter_age <= 60:
        return '60'
    return '90'


# @xray_recorder.capture('build_engine_data')
def build_engine_data(**kwargs):
    import re
    from decimal import Decimal

    daily_report = {}
    encounter_data = kwargs['encounter_data']
    encounters = [{
        'clientvisit_id': int(x['Service ID']),
        'rev_timeout': x['Service Date'],
        'transfer_date': x['Transfer Date'],
        'visit_type': x['Service Type'],
        'non_billable': x['Non Billable'] == 'True',
        'emp_id': int(x['Staff ID']),
        'client_id': int(x['Consumer ID']),
        'base_rate': Decimal(re.sub(r'[^\d.]', '', x['Base Rate'])),
        'data_dict_ids': 83
    } for x in encounter_data]
    unapproved_data = kwargs['unapproved_data']
    unapproved = [{
        'clientvisit_id': int(x['Service ID']),
        'rev_timeout': x['Service Date'],
        'visit_type': x['Service Type'],
        'non_billable': bool(x['Non Billable']),
        'emp_id': int(x['Staff ID']),
        'client_id': int(x['Consumer ID']),
        'red_x': x['Manual RedX Note'],
        'base_rate': Decimal(re.sub(r'[^\d.]', '', x['Base Rate']))
    } for x in unapproved_data]
    tx_plan_data = kwargs['tx_data']
    tx_plans = [{
        'rev_timeout': x['Service Date'],
        'emp_id':  int(x['Staff ID']),
        'client_id': int(x['Consumer ID'])
    } for x in tx_plan_data]
    da_data = kwargs['da_data']
    diagnostics = [{
        'rev_timeout': x['Service Date'],
        'emp_id': int(x['Staff ID']),
        'client_id': int(x['Consumer ID'])
    } for x in da_data]
    caseloads = kwargs['caseloads']
    for team_name, employees in caseloads.items():
        if team_name == 'unassigned':
            continue
        page_name = f'productivity_{team_name}'
        productivity_results = _build_team_productivity(employees, encounters, unapproved)
        daily_report[page_name] = productivity_results
    tx_report = _build_expiration_report(caseloads, tx_plans, 180)
    da_report = _build_expiration_report(caseloads, diagnostics, 180)
    thirty_sixty_ninety = _build_not_seen_report(caseloads, encounters)
    unassigned_report = _build_unassigned_report(caseloads)
    daily_report['tx_plans'] = tx_report
    daily_report['diagnostics'] = da_report
    daily_report['unassigned'] = unassigned_report
    daily_report['30, 60, 90'] = thirty_sixty_ninety
    daily_report['caseloads'] = caseloads
    return {'report_data': daily_report}
