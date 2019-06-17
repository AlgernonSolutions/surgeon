import re

from toll_booth.obj.incredible import parsers


def _filter_form_version(documentation):
    string = r'(<b>Form&nbsp;:&nbsp;Version:</b></td>(\s*)<td nowrap>)(?P<form>\d*)\s*:\s*(?P<version>\d*).*(</td>)'
    pattern = re.compile(string)
    matches = pattern.search(documentation)
    return matches.group('form'), matches.group('version')


class CredibleFormParser:
    def __init__(self, domain_name):
        self._domain_name = domain_name

    def parse(self, encounter_type: str, documentation: str):
        form_id, version_id = _filter_form_version(documentation)
        parsing_function = getattr(parsers, self._domain_name.lower())
        if not parsing_function:
            raise RuntimeError(f'no parser found for encounter_type: {encounter_type}')
        parsed_data = parsing_function(form_id, version_id, documentation)
        return parsed_data, form_id, version_id
