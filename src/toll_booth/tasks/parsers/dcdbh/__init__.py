import bs4

from toll_booth.tasks.parsers.dcdbh.split_header import _split_header
from toll_booth.tasks.parsers.dcdbh.tx_plan import _parse_tx_plans


def _make_tasty_soup(documentation):
    documentation_soup = bs4.BeautifulSoup(documentation, 'lxml')
    return documentation_soup


def _find_note_body(soup):
    tables = soup.find('body').find_all('table', recursive=False)
    for table in tables:
        return table


def _split_tx_plus(soup):
    tx_plus = soup.find_all('table', {'class': 'txplus'})
    return tx_plus


def _dissect_note_form(note_form):
    strings = [x for x in note_form.stripped_strings]
    return strings


def _dissect_note_header(note_header):
    strings = [x for x in note_header.stripped_strings]
    return strings


def _check_for_header_notes(tasty_soup):
    table_data = tasty_soup.find_all('td')
    for data in table_data:
        header = data.find_all('b', string='Notes:', recursive=False)
        if header:
            parent = data.parent
            strings = [x for x in parent.stripped_strings]
            return ' '.join(strings)


def _check_form_bookend(note_form_strings, bookend_start, bookend_finish):
    found = []
    for pointer, entry in enumerate(note_form_strings):
        if entry == bookend_start:
            segment = []
            for sub_entry in note_form_strings[pointer+1:]:
                if sub_entry == bookend_finish:
                    break
                segment.append(sub_entry)
            found.append(segment)
    return found


def _check_for_session_info(note_form_strings):
    bookend_start = 'Session Info (check box and enter notes about this session):'
    bookend_finish = 'Presenting Problem as stated during Enrollment  (From Consumer Profile):'
    results = _check_form_bookend(note_form_strings, bookend_start, bookend_finish)
    if len(results) > 1:
        raise RuntimeError('found multiple session infos')
    for result in results:
        return ' '.join(result)


def _check_for_patient_response(note_form_strings):
    bookend_start = 'Consumer\'s Response to session:'
    bookend_finish = 'Next appointment Scheduled?:'
    results = _check_form_bookend(note_form_strings, bookend_start, bookend_finish)
    if len(results) > 1:
        raise RuntimeError('found multiple patient responses')
    for result in results:
        return ' '.join(result)


def _invert_tx_documentation(tx_documentation):
    results = []
    for key, value in tx_documentation.items():
        if key == 'documentation':
            return [value]
        try:
            result = _invert_tx_documentation(value)
            if result:
                results.extend(result)
                results.append(key)
        except AttributeError:
            pass
    return results


def _generate_documentation_id(tx_plus_documentation):
    if not tx_plus_documentation:
        return ''
    if len(tx_plus_documentation) == 1:
        return ''
    next_entry = tx_plus_documentation[0]
    next_next_entry = tx_plus_documentation[1]
    try:
        return f'#{next_entry}#{next_next_entry}#{_generate_documentation_id(tx_plus_documentation[2:])}'
    except IndexError:
        return f'#{next_entry}#{next_next_entry}#'


def parser(documentation):
    results = {}
    soup = _make_tasty_soup(documentation)
    note_body = _find_note_body(soup)
    note_header, note_form = _split_header(note_body)
    tx_plus = _split_tx_plus(soup)
    if tx_plus:
        for plan in tx_plus:
            tx_plus_documentation = _parse_tx_plans(plan)
            inverted = _invert_tx_documentation(tx_plus_documentation)
            goal_first = list(reversed(inverted))
            documentation_id = _generate_documentation_id(goal_first)
            results[documentation_id] = inverted[0]
    if note_header:
        header_notes = _check_for_header_notes(soup)
        if header_notes:
            results['header_notes'] = header_notes
    if note_form:
        pieces = _dissect_note_form(note_form)
        session_info = _check_for_session_info(pieces)
        if session_info:
            results['session_info'] = session_info
        patient_response = _check_for_patient_response(pieces)
        if patient_response:
            results['patient_response'] = patient_response
    return results, 'credible_parser.v1'
