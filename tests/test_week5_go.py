from runners.drive.cards import week5_go as g


def test_native_goal_reader():
    assert g.fixture()['passed']


def test_nested_goal_sections_never_leak():
    text='---\nauthor: Constructed Writer\ntype: Standards Track\n---\n## Abstract\noutline\n## Motivation\ngoal\n### Detail\nHIDDEN_NESTED_GOAL\n## Specification\nvisible\n'
    row,reason=g.parse_document(text,'eips',b'x'*32)
    assert reason is None
    assert 'HIDDEN_NESTED_GOAL' in row['motivation']
    assert 'HIDDEN_NESTED_GOAL' not in row['rest']
    assert 'visible' in row['rest']


def test_fenced_heading_is_not_a_section():
    text='---\nauthor: Constructed Writer\n---\n## Motivation\ngoal\n```\n## Specification\nNOT_A_SECTION\n```\n## Specification\nvisible\n'
    row,_=g.parse_document(text,'eips',b'x'*32)
    assert 'NOT_A_SECTION' not in row['rest']


def test_absent_goal_is_counted():
    assert g.parse_document('PEP: 1\nAuthor: Name\n\nSpecification\n-------------\ntext','peps',b'x'*32)[1]=='no_motivation'
