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


## Add function `array_sort`

We need function `array_sort` to reduce the boilerplate when we need sorted
arrays.

Add change `array_sort`:

    sqitch add array_sort --note 'Add array_sort'

Edit `deploy/array_sort.sql` to contain the following function definition:

    CREATE FUNCTION array_sort(xs anycompatiblearray)
      RETURNS anycompatiblearray
      LANGUAGE sql
      IMMUTABLE LEAKPROOF
      AS $$ SELECT array_agg(x order by x) FROM (SELECT unnest(xs)) t(x) $$;

Commit change `array_sort`:

    git add .
    git commit -m 'Add array_sort'
