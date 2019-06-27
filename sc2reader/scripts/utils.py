# -*- coding: utf-8 -*-
from __future__ import absolute_import, print_function, unicode_literals, division

import argparse
import re
import textwrap


class Formatter(argparse.RawTextHelpFormatter):
    """FlexiFormatter which respects new line formatting and wraps the rest

    Example:
        >>> parser = argparse.ArgumentParser(formatter_class=FlexiFormatter)
        >>> parser.add_argument('a',help='''\
        ...     This argument's help text will have this first long line\
        ...     wrapped to fit the target window size so that your text\
        ...     remains flexible.
        ...
        ...         1. This option list
        ...         2. is still persisted
        ...         3. and the option strings get wrapped like this\
        ...            with an indent for readability.
        ...
        ...     You must use backslashes at the end of lines to indicate that\
        ...     you want the text to wrap instead of preserving the newline.
        ... ''')

    Only the name of this class is considered a public API. All the methods
    provided by the class are considered an implementation detail.
    """

    @classmethod
    def new(cls, **options):
        return lambda prog: Formatter(prog, **options)

    def _split_lines(self, text, width):
        lines = list()
        main_indent = len(re.match(r"( *)", text).group(1))
        # Wrap each line individually to allow for partial formatting
        for line in text.splitlines():

            # Get this line's indent and figure out what indent to use
            # if the line wraps. Account for lists of small variety.
            indent = len(re.match(r"( *)", line).group(1))
            list_match = re.match(r"( *)(([*-+>]+|\w+\)|\w+\.) +)", line)
            if list_match:
                sub_indent = indent + len(list_match.group(2))
            else:
                sub_indent = indent

            # Textwrap will do all the hard work for us
            line = self._whitespace_matcher.sub(" ", line).strip()
            new_lines = textwrap.wrap(
                text=line,
                width=width,
                initial_indent=" " * (indent - main_indent),
                subsequent_indent=" " * (sub_indent - main_indent),
            )

            # Blank lines get eaten by textwrap, put it back with [' ']
            lines.extend(new_lines or [" "])

        return lines
