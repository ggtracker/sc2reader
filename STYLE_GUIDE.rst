STYLE GUIDE
==============

As a rough style guide, please lint your code with black, codespell, and flake8::

    pip install black codespell flake8
    codespell -L queenland,uint
    flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
    flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics
    black . --check

More up-to-date checks may be detailed in `.circleci/config.yml`.

All files should start with the following::

    # -*- coding: utf-8 -*-
    #
    # Optional Documentation on the module
    #
    from __future__ import absolute_import, print_function, unicode_literals, division

All imports should be absolute.


All string formatting should be done in the following style::

    "my {0} formatted {1} string {2}".format("super", "python", "example")
    "the {x} style of {y} is also {z}".format(x="dict", y="arguments", z="acceptable")
