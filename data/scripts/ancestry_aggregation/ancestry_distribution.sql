-- Creates a `variants_af.csv` file containing the columns: frequency value, variants count, ancestry

SELECT
    annotations.af_afr,
    count(*) AS variant_count,
    'afr'
FROM variants
GROUP BY annotations.af_afr
ORDER BY annotations.af_afr
INTO OUTFILE 'variants_af.csv';

SELECT
    annotations.af_ami,
    count(*) AS variant_count,
    'ami'
FROM variants
GROUP BY annotations.af_ami
ORDER BY annotations.af_ami DESC
INTO OUTFILE 'variants_af.csv' APPEND;

SELECT
    annotations.af_amr,
    count(*) AS variant_count,
    'amr'
FROM variants
GROUP BY annotations.af_amr
ORDER BY annotations.af_amr DESC
INTO OUTFILE 'variants_af.csv' APPEND;

SELECT
    annotations.af_asj,
    count(*) AS variant_count,
    'asj'
FROM variants
GROUP BY annotations.af_asj
ORDER BY annotations.af_asj DESC
INTO OUTFILE 'variants_af.csv' APPEND;

SELECT
    annotations.af_eas,
    count(*) AS variant_count,
    'eas'
FROM variants
GROUP BY annotations.af_eas
ORDER BY annotations.af_eas DESC
INTO OUTFILE 'variants_af.csv' APPEND;

SELECT
    annotations.af_fin,
    count(*) AS variant_count,
    'fin'
FROM variants
GROUP BY annotations.af_fin
ORDER BY annotations.af_fin DESC
INTO OUTFILE 'variants_af.csv' APPEND;

SELECT
    annotations.af_nfe,
    count(*) AS variant_count,
    'nfe'
FROM variants
GROUP BY annotations.af_nfe
ORDER BY annotations.af_nfe DESC
INTO OUTFILE 'variants_af.csv' APPEND;

SELECT
    annotations.af_oth,
    count(*) AS variant_count,
    'oth'
FROM variants
GROUP BY annotations.af_oth
ORDER BY annotations.af_oth DESC
INTO OUTFILE 'variants_af.csv' APPEND;

SELECT
    annotations.af_sas,
    count(*) AS variant_count,
    'sas'
FROM variants
GROUP BY annotations.af_sas
ORDER BY annotations.af_sas DESC
INTO OUTFILE 'variants_af.csv' APPEND;

-- $ sort variants_af.csv > variants_af_sorted.csv
