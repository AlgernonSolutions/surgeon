import pytest

from toll_booth.tasks import surgical_tasks


@pytest.mark.engine_i
@pytest.mark.usefixtures('integration_environment')
class TestEngineCycle:
    def test_engine_cycle(self):
        id_source = 'PSI'
        results = surgical_tasks.cycle_engine(id_source)
        assert results
