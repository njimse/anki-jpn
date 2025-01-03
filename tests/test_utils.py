"""Unit tests for utility methods"""
import importlib.resources
import pytest
import js2py
import anki_jpn.resources

insert_ending_spans_text = importlib.resources.read_text(anki_jpn.resources, # pylint: disable=W4902
                                                         'insert_ending_spans.js')
insert_ending_spans = js2py.eval_js(insert_ending_spans_text)
insert_ending_spans_data = [
    ('foo', 'foobar', 'foo<span class=ending>bar</span>'),
    ('foo', 'bar', '<span class=ending>bar</span>'),
    ('foo', 'foo', 'foo'),
    ('foot', 'foobar', 'foo<span class=ending>bar</span>'),
    ('食べる', '食べます', '食べ<span class=ending>ます</span>'),
    ('<ruby><rb>食</rb><rt>た</rt></ruby>べる', '<ruby><rb>食</rb><rt>た</rt></ruby>べます',
        '<ruby><rb>食</rb><rt>た</rt></ruby>べ<span class=ending>ます</span>'),
    ('来る', '来ない', '来<span class=ending>ない</span>'),
    ('<ruby><rb>来</rb><rt>く</rt></ruby>る', '<ruby><rb>来</rb><rt>こ</rt></ruby>ない',
        '<ruby><rb>来</rb><rt><span class=ending>こ</span></rt></ruby><span class=ending>ない</span>'),
    ('<ruby><rb>歩</rb><rt>ある</rt></ruby>く', '<ruby><rb>歩</rb><rt>ある</rt></ruby>きます',
     '<ruby><rb>歩</rb><rt>ある</rt></ruby><span class=ending>きます</span>'),
    ('ある', 'ない', '<span class=ending>ない</span>'),
    ('<ruby><rb>食</rb><rt>た</rt></ruby>べる', '<ruby><rb>食</rb><rt>た</rt></ruby>べる',
     '<ruby><rb>食</rb><rt>た</rt></ruby>べる')
]
@pytest.mark.parametrize('dict_form, conj, ref_conjugation', insert_ending_spans_data)
def test_insert_ending_spans(dict_form, conj, ref_conjugation):
    """test the correctness of the Javascript function used to identify the difference
    between the dictionary and conjugated forms, inserting <span> tags to label the
    identified differences"""
    modified_conjugation = insert_ending_spans(dict_form, conj)
    assert modified_conjugation == ref_conjugation
