import pytest

from nbt import nbt
from nbtutils import str2nbt

BASIC_TYPE_TESTS = [
    ("1b", nbt.TAG_Byte, 1),
    ("1s", nbt.TAG_Short, 1),
    ("1", nbt.TAG_Int, 1),
    ("1l", nbt.TAG_Long, 1),
    ("1f", nbt.TAG_Float, 1),
    ("1d", nbt.TAG_Double, 1),
]

ARRAY_TYPE_TESTS = [
    ("[B; 1,2,3,4]", nbt.TAG_Byte_Array, bytearray([1,2,3,4])),
    ("[I; 1,2,3,4]", nbt.TAG_Int_Array, [1,2,3,4]),
    ("[L; 1,2,3,4]", nbt.TAG_Long_Array, [1,2,3,4]),
]

@pytest.mark.parametrize("text,tag_type,value", BASIC_TYPE_TESTS)
def test_basic_types(text, tag_type, value):
    val = str2nbt(text)
    assert isinstance(val, tag_type)
    assert val.value == value

@pytest.mark.parametrize("text,tag_type,value", ARRAY_TYPE_TESTS)
def test_array_types(text, tag_type, value):
    val = str2nbt(text)
    assert isinstance(val, tag_type)
    assert val.value == value

def test_string_type():
    val = str2nbt("hello")
    assert isinstance(val, nbt.TAG_String)
    assert val.value == "hello"
    val = str2nbt('"hello"')
    assert isinstance(val, nbt.TAG_String)
    assert val.value == "hello"

def test_list_type():
    lst = ["this","is","a","string","list"]
    lst_txt = "[" + ",".join(lst) + "]"
    val = str2nbt(lst_txt)
    assert isinstance(val, nbt.TAG_List)
    assert val.tagID == nbt.TAG_String.id
    assert all(isinstance(t, nbt.TAG_String) for t in val.tags)
    assert [t.value for t in val.tags] == lst

def test_compound_type():
    val = str2nbt("{a:1,b:2}")
    assert isinstance(val, nbt.TAG_Compound)
    assert type(val.tags[0]) == nbt.TAG_Int
    assert all(isinstance(t, nbt.TAG_Int) for t in val.tags)
    assert len(val.tags) == 2
    assert [t.name for t in val.tags] == ["a", "b"]
    assert [t.value for t in val.tags] == [1, 2]