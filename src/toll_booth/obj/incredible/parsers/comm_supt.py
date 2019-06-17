import re

import bs4


def _parse_tx_plan_node(tx_strings, starting_pointer):
    node = {}
    sliced_strings = tx_strings[starting_pointer:]
    end_words = ['Goal:', 'Objective:', 'Intervention:']
    if sliced_strings and sliced_strings[0] in end_words:
        sliced_strings = sliced_strings[1:]
    for pointer, entry in enumerate(sliced_strings):
        if entry == 'Start Date:':
            node['start_date'] = sliced_strings[pointer+1]
        if entry == 'Target Date:':
            target_date = sliced_strings[pointer+1]
            if target_date != 'End Date:':
                node['target_date'] = target_date
        if entry == 'End Date:':
            node['end_date'] = sliced_strings[pointer+1]
        if entry == 'Description':
            description = sliced_strings[pointer+1]
            if description != 'Tx Plus Extended Fields':
                node['description'] = sliced_strings[pointer+1]
        if entry == 'Documentation':
            documentation = []
            sub_section = sliced_strings[pointer+1:]
            for sub_pointer, documentation_string in enumerate(sub_section):
                if documentation_string in end_words:
                    try:
                        test_field = sub_section[sub_pointer+2]
                        if test_field == 'Start Date:':
                            break
                    except IndexError:
                        pass
                documentation.append(documentation_string)
            node['documentation'] = '\n'.join(documentation)
        if entry in end_words:
            return node
    return node


def _find_parent_start(tx_strings, starting_pointer, parent_name):
    potentials = list(reversed(tx_strings[:starting_pointer]))
    for pointer, entry in enumerate(potentials):
        if entry == parent_name:
            return potentials[pointer-1]


def _parse_tx_plan(documentation_soup):
    tx_plans = []
    tx_plus = documentation_soup.find_all('table', {'class': 'txplus'})
    for plan in tx_plus:
        tx_plan = {}
        tx_strings = [x for x in plan.stripped_strings]
        for pointer, entry in enumerate(tx_strings):
            if entry == 'Goal:':
                goal_name = tx_strings[pointer+1]
                goal = _parse_tx_plan_node(tx_strings, pointer)
                goal.update({'objectives': {}})
                tx_plan[goal_name] = goal
            if entry == 'Objective:':
                objective_name = tx_strings[pointer+1]
                goal_name = _find_parent_start(tx_strings, pointer, 'Goal:')
                existing_objectives = tx_plan[goal_name]['objectives']
                objective = _parse_tx_plan_node(tx_strings, pointer)
                objective.update({'interventions': {}})
                existing_objectives[objective_name] = objective
            if entry == 'Intervention:':
                try:
                    test_field = tx_strings[pointer+2]
                    if test_field != 'Start Date:':
                        continue
                except IndexError:
                    continue
                intervention_name = tx_strings[pointer + 1]
                goal_name = _find_parent_start(tx_strings, pointer, 'Goal:')
                objective_name = _find_parent_start(tx_strings, pointer, 'Objective:')
                existing_interventions = tx_plan[goal_name]['objectives'][objective_name]['interventions']
                intervention = _parse_tx_plan_node(tx_strings, pointer)
                existing_interventions[intervention_name] = intervention
        tx_plans.append(tx_plan)
    if len(tx_plans) > 1:
        raise RuntimeError(f'parsed an encounter to find it had two tx_plans in it, no idea boss')
    for entry in tx_plans:
        return entry
    return {'tx_plan': 'could not parse from documentation'}


def _find_symptoms_table(documentation_soup):
    tables = documentation_soup.find_all('table')
    for table in tables:
        table_rows = table.find_all('tr', recursive=False)
        for table_row in table_rows:
            table_data = table_row.find_all('td', recursive=False)
            for entry in table_data:
                bolds = entry.find_all('b', recursive=False)
                if bolds:
                    if 'Justification of Service' in [x.text for x in bolds]:
                        return table


def _filter_symptoms(documentation_soup):
    symptom_categories = {}
    symptoms_table = _find_symptoms_table(documentation_soup)
    if not symptoms_table:
        return {"unknown": "missing in documentation"}
    table_data = symptoms_table.find_all('td')
    table_strings = [x.text for x in table_data if x.text]
    category_pattern = re.compile(r'(Session:\s*)(?P<categories>.*)')
    symptom_pattern = re.compile(r'(How are the )(?P<symptom_category>.*)( symptoms presenting\?:\s*)(?P<symptoms>.*)')
    for pointer, entry in enumerate(table_strings):
        if 'Mental Health Symptoms Observed This Session:' in entry:
            category_matches = category_pattern.search(entry)
            symptom_types = category_matches.group('categories')
            split_types = symptom_types.split(', ')
            for split_type in split_types:
                split_type = split_type.strip()
                symptom_categories[split_type] = []
        if '?' in entry:
            symptom_matches = symptom_pattern.search(entry)
            if not symptom_matches:
                continue
            symptom_category = symptom_matches.group('symptom_category')
            symptoms = symptom_matches.group('symptoms')
            for split_type in symptoms.split(','):
                split_type = split_type.strip()
                for category in symptom_categories:
                    if symptom_category.lower() in category.lower():
                        symptom_categories[category].append(split_type)
    return symptom_categories


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


def _parse_454(documentation):
    documentation_soup = bs4.BeautifulSoup(documentation, 'lxml')
    tx_plan = _parse_tx_plan(documentation_soup)
    symptoms = _filter_symptoms(documentation_soup)
    return {'tx_plan': tx_plan, 'symptoms': symptoms}


def _parse_13(form_id, version_id, documentation):
    return {'response': _response_filter(form_id, version_id, documentation)}


def parse_comm_supt(form_id, version_id, documentation):
    if form_id in ['13', '454']:
        if version_id in ['5763', '5930', '5204']:
            return _parse_454(documentation)
    if form_id in ['13']:
        if version_id in ['5204']:
            return _parse_13(form_id, version_id, documentation)
    raise RuntimeError(f'do not know how to deal with form_version: {form_id}.{version_id}')
