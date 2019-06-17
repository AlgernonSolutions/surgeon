import logging

from aws_xray_sdk.core import xray_recorder


# @xray_recorder.capture('get_productivity_report_data')
def get_productivity_report_data(id_source, **kwargs):
    from toll_booth.obj import CredibleFrontEndDriver
    from datetime import datetime, timedelta

    logging.info(f'called a get_productivity report data, kwargs: {kwargs}')
    credible_date_format = '%m/%d/%Y'

    today = datetime.utcnow()
    encounter_start_date = today - timedelta(days=90)
    unapproved_start_date = today - timedelta(days=365)
    staff_search_data = {
        'emp_status_f': 'ACTIVE',
        'first_name': 1,
        'last_name': 1,
        'emp_id': 1,
        'profile_code': 1,
        'asgn_supervisors': 1,
        'asgn_supervisees': 1
    }
    client_search_data = {
        'teams': 1,
        'client_id': 1,
        'last_name': 1,
        'first_name': 1,
        'text28': 1,
        'dob': 1,
        'ssn': 1,
        'primary_assigned': 1,
        'client_status_f': 'ALL ACTIVE'
    }
    encounter_search_data = {
        'clientvisit_id': 1,
        'service_type': 1,
        'non_billable': 1,
        'consumer_name': 1,
        'staff_name': 1,
        'client_int_id': 1,
        'emp_int_id': 1,
        'non_billable1': 3,
        'visittype': 1,
        'orig_rate_amount': 1,
        'timein': 1,
        'wh_fld1': 'cv.transfer_date',
        'wh_cmp1': '>=',
        'wh_val1': encounter_start_date.strftime(credible_date_format),
        'data_dict_ids': 83
    }
    unapproved_search_data = encounter_search_data.copy()
    unapproved_search_data.update({
        'non_billable1': 0,
        'show_unappr': 1,
        'wh_fld1': 'cv.appr',
        'wh_cmp1': '=',
        'wh_val1': False,
        'data_dict_ids': 641
    })
    tx_plan_args = encounter_search_data.copy()
    tx_plan_args['visittype_id'] = 3
    da_args = encounter_search_data.copy()
    da_args['visittype_id'] = 5

    report_args = {
        'emp_data': ('Employees', staff_search_data),
        'client_data': ('Clients', client_search_data),
        'encounter_data': ('ClientVisit', encounter_search_data),
        'unapproved_data': ('ClientVisit', unapproved_search_data, unapproved_start_date, today),
        'tx_data': ('ClientVisit', tx_plan_args, unapproved_start_date, today),
        'da_data': ('ClientVisit', da_args, unapproved_start_date, today)
    }
    results = {}
    with CredibleFrontEndDriver(id_source) as driver:
        for report_name, report_arg in report_args.items():
            results[report_name] = driver.process_advanced_search(*report_arg)
    if not results:
        return
    return results
