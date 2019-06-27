Support
=========

For real-time support, please visit #sc2reader on the FreeNode.net IRC. For all other support please use the sc2reader@googlegroups.com mailing list or open an issue in the github tracker.

Issues
=========

Please include links to replays I can use to replicate. If an exception is being thrown while loading the replay please run the replay through the sc2parse script and post the output along with your issue. If it is a data quality issue please include a script of your own that can demonstrate the issue and the expected values.

If you can't share your code/replays publicly try to replicate with a smaller script or a replay you can share. If you can't even do that, say so in your issue and we can arrange to have materials sent privately.


Patches
=========

Please submit patches by pull request where possible. Patches should add a test to confirm their fix and should not break previously working tests.   Circle CI automatically runs tests on each pull request so please check https://circleci.com/gh/ggtracker/sc2reader to see the results of those tests.

If you are having trouble running/add/fixing tests for your patch let me know and I'll see if I can help.


Coding Style
==============

We'd like our code to follow PEP8 coding style in this project.
We use [python/black](https://github.com/python/black) in order to make our lives easier.
We propose you do the same within this project, otherwise you might be asked to
reformat your pull requests.

It's really simple just:

    pip install black
    black .

And [there are plugins for many editors](https://black.readthedocs.io/en/stable/editor_integration.html).
