import re

import bs4


def _notes_filter(documentation):
    notes = []
    soup = bs4.BeautifulSoup(documentation, "lxml")
    table_data = soup.find_all('td')
    for entry in table_data:
        if entry.text == 'Notes:':
            siblings = [x for x in entry.next_siblings]
            for element in siblings:
                if isinstance(element, bs4.NavigableString):
                    continue
                for piece in element.contents:
                    if piece.name == 'br':
                        notes.append('\n')
                        continue
                    if isinstance(piece, bs4.NavigableString):
                        notes.append(str(piece))
                        continue
                    notes.append(piece.text)
    return ' '.join(notes)


def _response_filter(form_id, version_id, documentation):
    pattern = r"(<td><span class='Answer'><span class='Answer'>)(?P<response>.*)(</span></span><tr><td>)"
    if form_id in ['13', '454']:
        if version_id in ['5763', '5930']:
            pattern = r"(<td><span class='Answer'>)(?P<response>.*)(</span>(&nbsp;)*</td>)"
        if version_id in ['5198']:
            pattern = r"(<td><span class='Answer'>)(?P<response>.+)(</span>(&nbsp;)*</td></tr>)"
    pattern = re.compile(pattern)
    matches = pattern.search(documentation)
    if not matches:
        raise RuntimeError(f'could not extract the response section from {form_id}.{version_id}')
    response = matches.group('response')
    response.replace('</br>', '\n')
    return response


def _parse_454(form_id, version__id, documentation):
    form_data = {
        'response': _response_filter(form_id, version__id, documentation),
        'notes': _notes_filter(documentation)
    }
    return form_data


def _parse_13(form_id, version__id, documentation):
    form_data = {
        'response': _response_filter(form_id, version__id, documentation),
        'notes': _notes_filter(documentation)
    }
    return form_data


def parse_day_treatment(form_id, version_id, documentation):
    if form_id == '454':
        if version_id == '5763':
            return _parse_454(form_id, version_id, documentation)
        if version_id == '5930':
            return _parse_454(form_id, version_id, documentation)
    if form_id == '13':
        if version_id == '5198':
            return _parse_13(form_id, version_id, documentation)
    raise RuntimeError(f'do not know how to deal with form_version: {form_id}.{version_id}')
