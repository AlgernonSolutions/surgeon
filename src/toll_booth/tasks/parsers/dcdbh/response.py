import re


def _response_filter(form_id, version_id, documentation):
    responses = set()
    patterns = [
        r"(<td><span class='Answer'><span class='Answer'>)(?P<response>.*)(</span></span><tr><td>)",
        r"(<td><span class='Answer'>)(?P<response>.+)(</span>(&nbsp;)*</td>)",
        r"(<td><span class='Answer'>)(?P<response>.+)(</span>(&nbsp;)*</td></tr>)"
    ]
    for pattern_string in patterns:
        pattern = re.compile(pattern_string)
        matches = pattern.search(documentation)
        if matches:
            response = matches.group('response')
            response.replace('</br>', '\n')
            if response:
                responses.add(response)
    if not responses:
        raise RuntimeError(f'could not extract the response section from {form_id}.{version_id}')
    if len(responses) > 1:
        raise RuntimeError(f'could not extract a single unique response section from {form_id}.{version_id}')
    for response in responses:
        return response