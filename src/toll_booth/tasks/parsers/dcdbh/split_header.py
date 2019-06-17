import re


def _test_for_header_buttons(table_row):
    forms = table_row.find_all('form', {'action': '/visit/clientvisit_view.asp'})
    return forms


def _test_for_header_links(table_row, test_pattern):
    links = table_row.find_all('a')
    targets = [x.attrs['href'] for x in links]
    target_string = ' '.join(targets)
    matches = test_pattern.search(target_string)
    if matches:
        return True
    return False


def _test_for_answer_search(table_row):
    inputs = table_row.find_all('input', id='searchString')
    if inputs:
        return True
    return False


def _split_header(note_body):
    header = None
    note_form = None
    table_rows = note_body.find_all('tr', recursive=False)
    header_link_pattern = re.compile(r'(/client/client_view\.asp).*(/employee/emp_view\.asp).*(/client/list_auth.asp)')
    for row in table_rows:
        button_check = _test_for_header_buttons(row)
        if button_check:
            continue
        link_check = _test_for_header_links(row, header_link_pattern)
        if link_check:
            if header:
                raise RuntimeError(f'found two headers for the same note')
            header = row
        answer_search_check = _test_for_answer_search(row)
        if answer_search_check:
            if note_form:
                raise RuntimeError(f'found two note bodies for the same note')
            note_form = row
    return header, note_form