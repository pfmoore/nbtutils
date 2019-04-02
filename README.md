Minecraft NBT data utilities
============================

This package extends the [nbt](https://pypi.org/project/NBT/) package for
manipulating Minecraft [NBT data](https://minecraft.gamepedia.com/NBT_format).

It adds functions to parse the "text" format of NBT data, and to generate the text
format from binary NBT data. It also includes a helper to generate a Python data
structure from NBT (using built in list and dictionary types rather than the
custom types provided by the `nbt` library).