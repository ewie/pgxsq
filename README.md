# pgxsq

pgxsq simplifies writing [Postgres extensions] \(especially those relying on
[procedural languages]) by managing changes with [Sqitch].

Tracking changes in Postgres extensions is not easy.  Updating procedures or
views requires copying the defintion and make the necessary changes.  This has
a major drawback: the changes made are not obvious without resorting to `diff`.
Wouldn't it be great to track changes in version control and use, for example,
just `git diff` to see what changes were made?

pgxsq allows that by tracking changes with [Sqitch] and generating extension
scripts from those changes.  Changes are made by [reworking][sqitch-rework]
the scripts that define the extension objects.  Sqitch caries out the grunt
work of tracking the original script version so that the script can be modified
and tracked in version control.  pgxsq builds the extension update paths from
the Sqitch [tags][sqitch-tag] that are required for reworking.


## Installation

Install with `pip`:

    pip install pgxsq

Install from source:

    make install

You also need to [install][sqitch-download] Sqitch to create projects and use
pgxsq.


## Development

    make


[Postgres extensions]: https://www.postgresql.org/docs/current/extend-extensions.html
[procedural languages]: https://www.postgresql.org/docs/current/xplang.html
[Sqitch]: https://sqitch.org
[sqitch-download]: https://sqitch.org/download/
[sqitch-rework]: https://sqitch.org/docs/manual/sqitch-rework/
[sqitch-tag]: https://sqitch.org/docs/manual/sqitch-rework/
