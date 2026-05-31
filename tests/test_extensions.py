from ambiguity.extensions import (
    BaseExtension, ExtensionResult, ExtensionRegistry, MaxWordCountExtension,
    get_registry,
)


def test_baseline_extension_noop():
    ext = BaseExtension()
    result = ext.on_pre_parse("test")
    assert not result.block
    assert result.score_modifier == 0.0
    assert result.annotations == []


def test_extension_name_default():
    ext = BaseExtension()
    assert ext.name() == "BaseExtension"


def test_max_word_count_blocks_above_threshold():
    ext = MaxWordCountExtension(max_words=3)
    result = ext.on_pre_parse("one two three four five")
    assert result.block is True
    assert "exceeds" in result.block_reason


def test_max_word_count_passes_below_threshold():
    ext = MaxWordCountExtension(max_words=10)
    result = ext.on_pre_parse("hello world")
    assert result.block is False


def test_max_word_count_at_threshold():
    ext = MaxWordCountExtension(max_words=5)
    result = ext.on_pre_parse("a b c d e")
    assert result.block is False


def test_max_word_count_name():
    ext = MaxWordCountExtension()
    assert ext.name() == "MaxWordCountExtension"


def test_registry_register_and_all():
    reg = ExtensionRegistry()
    assert reg.all() == []
    ext = MaxWordCountExtension(max_words=10)
    reg.register(ext)
    assert len(reg.all()) == 1
    assert reg.all()[0] is ext


def test_registry_pre_parse():
    reg = ExtensionRegistry()
    ext = MaxWordCountExtension(max_words=3)
    reg.register(ext)
    results = reg.pre_parse("one two three four")
    assert len(results) == 1
    assert results[0].block is True


def test_registry_pre_parse_empty():
    reg = ExtensionRegistry()
    results = reg.pre_parse("hello")
    assert results == []


def test_get_registry_singleton():
    r1 = get_registry()
    r2 = get_registry()
    assert r1 is r2


def test_all_extension_hooks_return_extension_result():
    ext = BaseExtension()
    assert isinstance(ext.on_pre_parse(""), ExtensionResult)
    assert isinstance(ext.on_post_parse({}), ExtensionResult)
    assert isinstance(ext.on_pre_score({}), ExtensionResult)
    assert isinstance(ext.on_post_score({}), ExtensionResult)
