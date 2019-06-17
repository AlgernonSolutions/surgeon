import pytest
import rapidjson

from toll_booth import handler


@pytest.mark.parser_i
@pytest.mark.usefixtures('integration_environment')
class TestGraphTasks:
    def test_parse_documentation(self, mock_context, retrieve_queued_sns_event):
        event = retrieve_queued_sns_event('documentation_parser_event')
        results = handler(event, mock_context)
        for result in results:
            parsed_results = rapidjson.loads(result)
            assert parsed_results
