def _parse_tx_plan_node(tx_strings, starting_pointer):
    node = {}
    sliced_strings = tx_strings[starting_pointer:]
    end_words = ['Goal:', 'Objective:', 'Intervention:']
    if sliced_strings and sliced_strings[0] in end_words:
        sliced_strings = sliced_strings[1:]
    for pointer, entry in enumerate(sliced_strings):
        if entry == 'Start Date:':
            node['start_date'] = sliced_strings[pointer + 1]
        if entry == 'Target Date:':
            target_date = sliced_strings[pointer + 1]
            if target_date != 'End Date:':
                node['target_date'] = target_date
        if entry == 'End Date:':
            node['end_date'] = sliced_strings[pointer + 1]
        if entry == 'Description':
            description = sliced_strings[pointer + 1]
            if description != 'Tx Plus Extended Fields':
                node['description'] = sliced_strings[pointer + 1]
        if entry == 'Documentation':
            documentation = []
            sub_section = sliced_strings[pointer + 1:]
            for sub_pointer, documentation_string in enumerate(sub_section):
                if documentation_string in end_words:
                    try:
                        test_field = sub_section[sub_pointer + 2]
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
            return potentials[pointer - 1]


def _parse_tx_plans(tx_plus):
    tx_plan = {'goal': {}}
    tx_strings = [x for x in tx_plus.stripped_strings]
    for pointer, entry in enumerate(tx_strings):
        if entry == 'Goal:':
            goal_name = tx_strings[pointer + 1]
            goal = _parse_tx_plan_node(tx_strings, pointer)
            goal.update({'objective': {}})
            tx_plan['goal'][goal_name] = goal
        if entry == 'Objective:':
            objective_name = tx_strings[pointer + 1]
            goal_name = _find_parent_start(tx_strings, pointer, 'Goal:')
            existing_objectives = tx_plan['goal'][goal_name]['objective']
            objective = _parse_tx_plan_node(tx_strings, pointer)
            objective.update({'intervention': {}})
            existing_objectives[objective_name] = objective
        if entry == 'Intervention:':
            try:
                test_field = tx_strings[pointer + 2]
                if test_field != 'Start Date:':
                    continue
            except IndexError:
                continue
            intervention_name = tx_strings[pointer + 1]
            goal_name = _find_parent_start(tx_strings, pointer, 'Goal:')
            objective_name = _find_parent_start(tx_strings, pointer, 'Objective:')
            existing_interventions = tx_plan['goal'][goal_name]['objective'][objective_name]['intervention']
            intervention = _parse_tx_plan_node(tx_strings, pointer)
            existing_interventions[intervention_name] = intervention
    return tx_plan
