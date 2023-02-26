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


## Release `array_util 0.1`

Extension `array_util` does not offer much at this point but we want to get
some feedback.  Let's release version `0.1` by tagging the last change:

    sqitch tag 0.1 --note 'Release 0.1'

Commit release `0.1`:

    git add -u
    git commit -m 'Release 0.1'


## Build and test `array_util 0.1`

We need to build the actual extension files.  Run `pgxsq` and let it write the
extension files to `ext`:

    pgxsq --dest ext

Add the extension files of `array_util` to Postgres:

    cp -t "$(pg_config --sharedir)"/extension \
      ext/array_util.control \
      ext/array_util--0.1.sql

Notice that `pgxsq` created empty control file `array_util.control` which is
enough for this example.  But in general you would modify the control file as
necessary for your particular extension.

Connect with `psql` to database `test`, install `array_util` version `0.1`,
and check that `array_sort` works:

    test=# CREATE EXTENSION array_util VERSION '0.1';
    CREATE EXTENSION
    test=# SELECT array_sort(array[1,3,2]);
     array_sort
    ------------
     {1,2,3}
    (1 row)
