\echo Use "CREATE EXTENSION array_util" to load this file. \quit
CREATE FUNCTION array_sort(xs anycompatiblearray)
  RETURNS anycompatiblearray
  LANGUAGE sql
  IMMUTABLE LEAKPROOF
  AS $$ SELECT array_agg(x order by x) FROM (SELECT unnest(xs)) t(x) $$;
