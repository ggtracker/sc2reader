STYLE GUIDE
==============

As a rough style guide, please lint your code with pep8::

    pip install pep8
    pep8 --ignore E501,E226,E241 sc2reader


All files should start with the following::

    # -*- coding: utf-8 -*-
    #
    # Optional Documentation on the module
    #
    from __future__ import absolute_import, print_function, unicode_literals, division

All imports should be absolute.


All string formatting sound be done in the following style::

    "my {0} formatted {1} string {2}".format("super", "python", "example")
    "the {x} style of {y} is also {z}".format(x="dict", y="arguments", z="acceptable")

The format argument index numbers are important for 2.6 support. ``%`` formatting is not allowed for 3.x support

