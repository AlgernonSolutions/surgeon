import pytest

from toll_booth.tasks import graph_tasks


@pytest.mark.graph_tasks_i
@pytest.mark.usefixtures('integration_environment')
class TestGraphTasks:
    def test_parse_documentation(self, comm_supt_data):
        results = graph_tasks.work_comm_supt_documentation(*comm_supt_data)
        assert results
