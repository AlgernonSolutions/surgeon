import bs4

from toll_booth.tasks.parsers.dcdbh import _parse_tx_plan, _filter_symptoms, _response_filter, _notes_filter


def _parse_454(form_id, version_id, documentation):
    if version_id == '5763':
        documentation_soup = bs4.BeautifulSoup(documentation, 'lxml')
        tx_plan = _parse_tx_plan(documentation_soup)
        symptoms = _filter_symptoms(documentation_soup)
        return {'tx_plan': tx_plan, 'symptoms': symptoms}, form_id, version_id
    form_data = {
        'response': _response_filter(form_id, version_id, documentation),
        'notes': _notes_filter(documentation)
    }
    return form_data, form_id, version_id


def _parse_13(form_id, version_id, documentation):
    form_data = {
        'response': _response_filter(form_id, version_id, documentation),
        'notes': _notes_filter(documentation)
    }
    return form_data, form_id, version_id