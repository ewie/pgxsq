SELECT
  array_sort('{}'::text[]),
  array_sort('{}'::text[], false)
WHERE false;
