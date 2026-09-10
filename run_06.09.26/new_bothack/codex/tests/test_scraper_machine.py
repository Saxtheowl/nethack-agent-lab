"""Compare ordered original send calls across complete synchronization traces."""
from dataclasses import asdict, is_dataclass, replace
import pytest
from bothack.frame import Frame
from bothack.position import Position
from bothack.scraper import Scraper

pytestmark = pytest.mark.oracle


def screen(top='', x=40, y=10, rows=None, status=True):
    lines = [top] + [''] * 23
    for row, text in (rows or {}).items():
        lines[row] = text
    if status:
        lines[22] = 'Bot the Stripling St:18 Dx:12 Co:18 In:8 Wi:10 Ch:7 Lawful S:0'
        lines[23] = 'Dlvl:1 $:0 HP:16(16) Pw:2(2) AC:6 Xp:1/0 T:1 '
    return Frame.text(lines, Position(x, y))


def plain(value):
    if is_dataclass(value):
        return plain(asdict(value))
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}
    if isinstance(value, (tuple, list)):
        return [plain(v) for v in value]
    return value


def compare(oracle, frames, no_mark=None):
    scraper = Scraper(no_mark)
    actual, steps = [], []
    for frame in frames:
        if isinstance(frame, tuple):
            scraper = Scraper(frame[1])
            steps.append(frame)
            actual.append([])
        else:
            steps.append(('frame', plain(frame)))
            actual.append(plain(scraper.feed(frame)))
    expected = oracle.call('scraper-trace', no_mark, steps)
    for index, (a, e) in enumerate(zip(actual, expected)):
        assert a == e, f'trace step {index}: {a!r} != {e!r}'


def synchronization(message='You see here a dagger.'):
    return [screen(), screen("# #'", 4, 0), screen(), screen('# #'),
            screen('# #', 41), screen(message, 41), screen(message, 41)]


def test_mark_and_sink(oracle):
    compare(oracle, synchronization() + [('reset', None)] + synchronization(''))


def test_repeated_markers_wait_for_final_redraw(oracle):
    # Claude's real hallucination replay exposed early decisions on a marker.
    # Compare to Clojure, with changing monsters but an unchanged player cursor.
    frames = synchronization()[:4] + [
        screen('# #', rows={10: ' ' * 42 + glyph}) for glyph in ('d', 'D', 'L')
    ] + [screen('', rows={10: ' ' * 42 + 'n'}), screen('')]
    compare(oracle, frames)
    scraper = Scraper()
    calls = [scraper.feed(frame) for frame in frames]
    assert not any(call[0] == 'full-frame' for step in calls[:7] for call in step)
    assert any(call[0] == 'full-frame' for step in calls[7:] for call in step)


def test_escape_extended_command(oracle):
    compare(oracle, [screen(), screen("# '", 3, 0), screen('Unknown extended command.')])


def test_farming(oracle):
    compare(oracle, [screen('Waiting'), *synchronization()[1:]], False)


@pytest.mark.parametrize('prefix', ['', 'What do you want to zap? [a-z]'])
def test_direction(oracle, prefix):
    compare(oracle, [screen(prefix, len(prefix) + 1, 0), screen('In wh', 5, 0),
                     screen('In what direction?', 19, 0), *synchronization()], prefix)


@pytest.mark.parametrize('message', [
    'What do you want to eat? [a-z or ?*]',
    'There is a food ration here; eat it? [yn] (n)',
    'What do you want to use or apply? [a-z or ?*]',
])
def test_choice_repeated(oracle, message):
    frame = screen(message, len(message) + 1, 0)
    compare(oracle, [frame, frame, *synchronization()])


def test_marked_text_prompt(oracle):
    message = 'For what do you wish?'
    compare(oracle, [screen(message, len(message) + 1, 0),
                     screen(message + " ##'", len(message) + 4, 0)])


@pytest.mark.parametrize('message', [
    'Where do you want to travel to? (For instructions type a ?)',
    'To what location? (For instructions type a ?)',
    'Pay whom? (For instructions type a ?)',
])
def test_location(oracle, message):
    compare(oracle, [screen(message)], '')


def test_more_lists_and_flush(oracle):
    more = screen('There is a fountain here.', 9, 5,
                  {1: '', 2: 'Things that are here:', 3: 'a dagger', 4: 'a food ration', 5: ' --More--'})
    compare(oracle, [more, *synchronization()])


@pytest.mark.parametrize('message', [
    'You hit the goblin!', "You don't have that object.",
    'You wrest one last charge from the wand.',
    'To what position do you want to be teleported?',
    'Sayonara level 10.', 'Farvel Bot, welcome to NetHack!',
    'Goodbye Bot the Valkyrie...',
])
def test_more_messages(oracle, message):
    top = message + '--More--'
    compare(oracle, [screen(top, len(top), 0)])


def menu(head, page=1, last=1, slot='a', item='a dagger'):
    footer = '(end) ' if last == 1 else f'({page} of {last})'
    return screen(head or f'{slot} - {item}', len(footer), 4,
                  {2: f'{slot} - {item}', 4: footer}, status=False)


@pytest.mark.parametrize('head', ['Pick up what?', 'What would you like to identify first?',
                                 'Pick a skill to advance:', 'What do you wish to do?'])
def test_single_menu(oracle, head):
    compare(oracle, [menu(head), *synchronization()])


@pytest.mark.parametrize('head', ['Pick up what?', 'What would you like to identify first?'])
def test_paged_menu(oracle, head):
    first = menu(head, 1, 2)
    last = menu('', 2, 2, 'b', 'a food ration')
    compare(oracle, [first, last, last, first, first, last, *synchronization()])


def test_inventory_without_heading(oracle):
    f = menu('a - a dagger')
    colors = list(f.colors)
    colors[0] = ('inverse',) + (None,) * 79
    compare(oracle, [replace(f, colors=tuple(colors))])


def test_game_start_and_end(oracle):
    prompt = 'Shall I pick a character for you? [ynq] '
    compare(oracle, [screen('', len(prompt), 3, {1: 'NetHack, Copyright 1985-2003', 3: prompt}),
                     screen('Do you want your possessions identified? [yn]')])


def test_blank_menu_first_line_rejected(oracle):
    from bothack.scraper import menu_options
    frame = screen('', 6, 4, {2: 'a - a dagger', 4: '(end) '}, status=False)
    with pytest.raises(IndexError):
        menu_options(frame)
    with pytest.raises(RuntimeError, match='IndexOutOfBoundsException'):
        oracle.call('scraper-trace', None, [('frame', plain(frame))])


@pytest.mark.parametrize('frame', [menu('Unrecognized menu'),
                                  screen('Unrecognized question? [yn]', 28, 0)])
def test_failed_redraw_rolls_back(frame):
    scraper = Scraper()
    before = scraper.__dict__.copy()
    with pytest.raises(NotImplementedError):
        scraper.feed(frame)
    assert scraper.__dict__ == before
