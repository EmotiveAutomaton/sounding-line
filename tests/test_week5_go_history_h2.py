from collections import Counter
from runners.drive.cards import week5_go_history_h2 as h


def test_strict_utf8_and_declared_legacy_encoding_only():
    c=Counter()
    assert h.decode_blob('café'.encode(),c)=='café'
    assert h.decode_blob(b'\xef\xbb\xbfcafe',c)=='cafe'
    assert h.decode_blob(b'coding: latin-1\ncaf\xe9',c)=='coding: latin-1\ncafé'
    assert h.decode_blob(b'caf\xe9',c)==''
    assert h.decode_blob(b'coding: unsupported\ncaf\xe9',c)==''
    assert c['explicit_legacy_encoding_versions']==1 and c['excluded_undeclared_or_unsupported_encoding_versions']==2
    assert h.decode_blob(b'caf\0e',c)=='' and c['excluded_binary_versions']==1


def test_unknown_versions_are_window_barriers():
    edits=[{'rest_changed':True,'added':'before'},None,{'unreadable_gap':True},
           {'rest_changed':True,'added':'after'}]
    assert h.window(edits)==['before']
    assert h.window(edits,True)==['after']
