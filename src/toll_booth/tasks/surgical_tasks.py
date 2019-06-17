import logging

from toll_booth.tasks import credible_fe_tasks


def cycle_engine(id_source):
    logging.info(f'started a cycle of the surgical engine for id_source: {id_source}')
    task_kwargs = {'id_source': id_source}
    tasks = [
        credible_fe_tasks.get_productivity_report_data,
        credible_fe_tasks.build_clinical_teams,
        credible_fe_tasks.build_clinical_caseloads,
        credible_fe_tasks.build_engine_data
    ]
    for task in tasks:
        task_data = task(**task_kwargs)
        task_kwargs.update(task_data)
    return task_data
