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