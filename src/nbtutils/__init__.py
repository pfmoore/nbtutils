import functools
import re

from nbt import nbt
import pyparsing as pp

__all__ = [
    'str2nbt',
    'nbt2str',
    'nbt2py',
]

# Converting text format NBT data to in-memory form

def skipLiteral(lit):
    return pp.Literal(lit).suppress()

def delimited(parser, start, end, allow_empty=True):
    if allow_empty:
        parser = pp.Optional(parser)
    ret = skipLiteral(start) + parser + skipLiteral(end)
    return ret

def matchDict(key, val, pre='{', suf='}', sep=',', delim=':', allowTrailingSep=False):
    kv = key + skipLiteral(delim) + val
    kv.setParseAction(lambda t: (t[0], t[1]))
    kv_seq = kv + pp.ZeroOrMore(skipLiteral(sep) + kv)
    if allowTrailingSep:
        kv_seq = kv_seq + pp.Optional(skipLiteral(seq))
    dict_parser = delimited(kv_seq, start=pre, end=suf)
    dict_parser.setParseAction(lambda t: dict(t.asList()))
    dict_parser.setName("Dictionary")
    return dict_parser

def matchNumber(suffix='', is_float=False):
    if is_float:
        rex = r"[+-]?\d+(?:\.\d*)?(?:e[+-]?\d+)?"
    else:
        rex = r"[-+]?\d+"
    rex = "(" + rex + ")"
    if suffix:
        rex = rex + suffix
    number = pp.Regex(rex, flags=re.IGNORECASE).sub(r"\1")
    if is_float:
        # Add a parse action, as sub() is also a parse action
        number.addParseAction(lambda t: float(t[0]))
    else:
        # Add a parse action, as sub() is also a parse action
        number.addParseAction(lambda t: int(t[0]))
    name = "Num"
    if suffix:
        name += "[" + suffix + "]"
    number.setName(name)
    return number

def matchNumList(typecode):
    numlist = (
        pp.Suppress(pp.Literal('[') + pp.Literal(typecode) + pp.Literal(';')) +
        pp.delimitedList(matchNumber(suffix=typecode + '?')) +
        pp.Suppress(pp.Literal(']'))
    )
    numlist.setParseAction(lambda t: tuple(t))
    numlist.setName("NumList[{}]".format(typecode))
    return numlist

# ---------------------------------------------------------------------- 

STR_TAG = pp.Forward()

STR_Byte = matchNumber(suffix='b')
STR_Short = matchNumber(suffix='s')
STR_Int = matchNumber()
STR_Long = matchNumber(suffix='l')
STR_Float = matchNumber(suffix='f', is_float=True)
STR_Double = matchNumber(suffix='d?', is_float=True)
STR_String = pp.Word(pp.alphanums) ^ pp.QuotedString('"')

# Use the longest match when matching numbers, as some forms can
# be prefixes of other forms - 1 vs 1.0 vs 1.0f, for example.
STR_Number = pp.Or([
    STR_Byte,
    STR_Short,
    STR_Int,
    STR_Long,
    STR_Float,
    STR_Double,
])

STR_Byte_Array = matchNumList('B')
STR_Int_Array = matchNumList('I')
STR_Long_Array = matchNumList('L')

STR_List = delimited(pp.delimitedList(STR_TAG).setParseAction(lambda t: tuple(t)), start='[', end=']')
STR_Compound = matchDict(STR_String, STR_TAG)

STR_TAG << (
    STR_Number | STR_String |
    STR_Byte_Array | STR_Int_Array | STR_Long_Array | STR_List | STR_Compound
)

# ---------------------------------------------------------------------- 

STR_Byte.addParseAction(lambda t: nbt.TAG_Byte(t[0]))
STR_Short.addParseAction(lambda t: nbt.TAG_Short(t[0]))
STR_Int.addParseAction(lambda t: nbt.TAG_Int(t[0]))
STR_Long.addParseAction(lambda t: nbt.TAG_Long(t[0]))
STR_Float.addParseAction(lambda t: nbt.TAG_Float(t[0]))
STR_Double.addParseAction(lambda t: nbt.TAG_Double(t[0]))
STR_String.addParseAction(lambda t: nbt.TAG_String(t[0]))

def make_tag_array(vals, tag_type, value_constructor=list):
    tag = tag_type()
    tag.value = value_constructor(vals)
    return tag

STR_Byte_Array.addParseAction(lambda t: make_tag_array(t[0], nbt.TAG_Byte_Array, value_constructor=bytearray))
STR_Int_Array.addParseAction(lambda t: make_tag_array(t[0], nbt.TAG_Int_Array))
STR_Long_Array.addParseAction(lambda t: make_tag_array(t[0], nbt.TAG_Long_Array))

def make_tag_list(vals):
    tag = nbt.TAG_List(type=vals[0])
    tag.tags = list(vals)
    return tag

STR_List.addParseAction(lambda t: make_tag_list(t[0]))

def make_tag_compound(value):
    tag = nbt.TAG_Compound()
    for k, v in value.items():
        v.name = k.value
        tag.tags.append(v)
    return tag

STR_Compound.addParseAction(lambda t: make_tag_compound(t[0]))

# ---------------------------------------------------------------------- 

def str2nbt(s):
    return STR_TAG.parseString(s, parseAll=True)[0]

# ---------------------------------------------------------------------- 

# Converting NBT data held in memory into a text format

@functools.singledispatch
def nbt2str(nbtdata):
    pass

@nbt2str.register
def _(nbtdata : nbt.TAG_Byte):
    return str(nbtdata.value) + "b"

@nbt2str.register
def _(nbtdata : nbt.TAG_Short):
    return str(nbtdata.value) + "s"

@nbt2str.register
def _(nbtdata : nbt.TAG_Int):
    return str(nbtdata.value)

@nbt2str.register
def _(nbtdata : nbt.TAG_Long):
    return str(nbtdata.value) + "l"

@nbt2str.register
def _(nbtdata : nbt.TAG_Float):
    return str(nbtdata.value) + "f"

@nbt2str.register
def _(nbtdata : nbt.TAG_Double):
    return str(nbtdata.value) + "d"

@nbt2str.register
def _(nbtdata : nbt.TAG_String):
    return '"' + str(nbtdata.value) + '"'

@nbt2str.register
def _(nbtdata : nbt.TAG_Byte_Array):
    content = ",".join([str(v) for v in nbtdata.value])
    return "[B; " + content + "]"

@nbt2str.register
def _(nbtdata : nbt.TAG_Int_Array):
    content = ",".join([str(v) for v in nbtdata.value])
    return "[I; " + content + "]"

@nbt2str.register
def _(nbtdata : nbt.TAG_Long_Array):
    content = ",".join([str(v) for v in nbtdata.value])
    return "[L; " + content + "]"

@nbt2str.register
def _(nbtdata : nbt.TAG_List):
    content = ",".join([nbt2str(tag) for tag in nbtdata.tags])
    return "[" + content + "]"

@nbt2str.register
def _(nbtdata : nbt.TAG_Compound):
    parts = []
    for tag in nbtdata.tags:
        text = '"' + tag.name + '":' + nbt2str(tag)
        parts.append(text)
    return "{" + ','.join(parts) + "}"

# ---------------------------------------------------------------------- 

# Converting NBT data held in memory into Python data objects

@functools.singledispatch
def nbt2py(nbtdata):
    pass

@nbt2py.register
def _(nbtdata : nbt.TAG_Byte):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_Short):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_Int):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_Long):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_Float):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_Double):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_String):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_Byte_Array):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_Int_Array):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_Long_Array):
    return nbtdata.value

@nbt2py.register
def _(nbtdata : nbt.TAG_List):
    return [nbt2py(tag) for tag in nbtdata.tags]

@nbt2py.register
def _(nbtdata : nbt.TAG_Compound):
    return {tag.name: nbt2py(tag) for tag in nbtdata.tags}