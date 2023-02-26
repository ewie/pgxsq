BEGIN;

DROP FUNCTION array_sort(xs anycompatiblearray);

CREATE FUNCTION array_sort(xs anycompatiblearray, reverse bool = false)
  RETURNS anycompatiblearray
  LANGUAGE sql
  IMMUTABLE LEAKPROOF
  AS $$
    SELECT
      CASE WHEN reverse
        THEN array_agg(x order by x desc)
        ELSE array_agg(x order by x)
      END
    FROM (SELECT unnest(xs)) t(x)
  $$;

COMMIT;
