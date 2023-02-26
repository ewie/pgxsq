# pgxsq example `array_util`

This example shows how to create extension `array_util` with Sqitch and pgxsq.
Extension `array_util` will provide array functions missing from the Postgres
core.

You can also follow the steps by checking `git log` in the directory of this
README.


## Create Sqitch project `array_util`

Create a new Sqitch project `array_util` using the Postgres engine:

    sqitch init array_util --engine pg

Commit the Sqitch project:

    git add .
    git commit -m 'Create array_util'
