STYLE GUIDE
==============

As a rough style guide, please lint your code with black, codespell, and ruff::

    pip install black codespell ruff
    codespell -L queenland,uint
    ruff .
    black . --check

More up-to-date checks may be detailed in `.circleci/config.yml`.

All files should start with the following::

    # -*- coding: utf-8 -*-
    #
    # Optional Documentation on the module
    #
    from __future__ import absolute_import, print_function, unicode_literals, division

All imports should be absolute.

All string formatting should be done with f-strings. See https://docs.python.org/3/reference/lexical_analysis.html#f-strings
