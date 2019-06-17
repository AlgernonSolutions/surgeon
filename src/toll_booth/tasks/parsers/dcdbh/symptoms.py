import re


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