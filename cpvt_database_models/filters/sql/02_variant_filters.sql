DELETE
FROM kv_store
WHERE key = 'filters:variants';

--- NEW STATEMENT

WITH provenance
         AS (SELECT build_ui_filter(jsonb_agg(d), 'checkboxes',
                                    'provenance',
                                    'Provenance', 1) AS provenance
             FROM (SELECT dataset_id AS value,
                          name       AS label
                   FROM variants_dataset) AS d),

     -- filters on edit type
     edit_type
         AS (SELECT build_ui_filter(jsonb_agg(e), 'checkboxes', 'editType',
                                    'Consequence Type', 2,
                                    description := 'The consequence of a variant to the genome or protein sequence.'
                    ) AS edit_type

             FROM (SELECT DISTINCT edit_type_id AS value,
                                   name         AS label
                   FROM edit_type) AS e),


     clinical_significance
         AS (SELECT build_ui_filter(jsonb_agg(c), 'checkboxes',
                                    'clinicalSignificance',
                                    'Clinical Significance',
                                    3,
                                    description :=
                                        'The clinical significance of a variant is a classification of the variant ' ||
                                        'based on its potential impact on health calculated by the NCBI in the ClinVar database.'
                    ) AS clinical_significance

             FROM (SELECT DISTINCT clinical_significance_id AS value,
                                   clinical_significance    AS label
                   FROM clinical_significance) AS c),

     num_individuals_hist AS (SELECT jsonb_agg(h) AS histogram
                              FROM (WITH n_bins AS (SELECT 30 AS n),
                                         ranges
                                             AS (SELECT MIN(num_individuals) AS min_val,
                                                        MAX(num_individuals) AS max_val
                                                 FROM variant_num_individuals_v),
                                         bins
                                             AS (SELECT generate_series(1,
                                                                        (SELECT n
                                                                         FROM n_bins)) AS bin),
                                         histogram
                                             AS (SELECT width_bucket(
                                                                num_individuals,
                                                                min_val + 1,
                                                                max_val + 1,
                                                                (SELECT n
                                                                 FROM n_bins)) AS bin,
                                                        ROUND(
                                                                LOG(COUNT(variant_id) + 1)::numeric,
                                                                2)             AS freq
                                                 FROM variant_num_individuals_v,
                                                      ranges
                                                 GROUP BY bin)
                                    SELECT bins.bin,
                                           COALESCE(histogram.freq, 0) AS freq
                                    FROM bins
                                             LEFT JOIN
                                         histogram ON bins.bin = histogram.bin
                                    ORDER BY bins.bin) h),

     num_individuals
         AS (SELECT build_ui_filter(jsonb_agg(v), 'range', 'numIndividuals',
                                    'Number of Individuals', 4,
                                    (SELECT histogram
                                     FROM num_individuals_hist)
                    ) AS num_individuals
             FROM (SELECT MAX(num_individuals) AS max,
                          MIN(num_individuals) AS min
                   FROM variant_num_individuals_v) v),

     avg_age_of_onset_cpvt_histogram AS (SELECT jsonb_agg(h) AS histogram
                                         FROM (WITH n_bins AS (SELECT 50 AS n),
                                                    ranges
                                                        AS (SELECT MIN(avg_age_of_onset_cpvt)     AS min_val,
                                                                   MAX(avg_age_of_onset_cpvt) + 1 AS max_val
                                                            FROM variant_view_mv),
                                                    bins
                                                        AS (SELECT generate_series(
                                                                           1,
                                                                           (SELECT n
                                                                            FROM n_bins)
                                                                   ) AS bin),
                                                    histogram
                                                        AS (SELECT width_bucket(
                                                                           avg_age_of_onset_cpvt,
                                                                           min_val,
                                                                           max_val,
                                                                           (SELECT n
                                                                            FROM n_bins)
                                                                   )                 AS bin,
                                                                   COUNT(variant_id) AS freq
                                                            FROM variant_view_mv,
                                                                 ranges
                                                            WHERE variant_view_mv.num_individuals >= 1
                                                            GROUP BY bin)
                                               SELECT bins.bin,
                                                      COALESCE(histogram.freq, 0) AS freq
                                               FROM bins
                                                        LEFT JOIN
                                                    histogram ON bins.bin = histogram.bin
                                               ORDER BY bins.bin) h),

     avg_age_of_onset_cpvt
         AS (SELECT build_ui_filter(jsonb_agg(v), 'range', 'avgAgeOfOnsetCpvt',
                                    'Average Age of Onset of CPVT', 5,
                                    (SELECT histogram
                                     FROM avg_age_of_onset_cpvt_histogram),
                                    description := 'Age of onset is the age at which the first symptoms of CPVT were observed.'
                    ) AS avg_age_of_onset_cpvt

             FROM (SELECT CEIL(MAX(avg_age_of_onset_cpvt))  AS max,
                          FLOOR(MIN(avg_age_of_onset_cpvt)) AS min
                   FROM variant_view_mv
                   WHERE avg_age_of_onset_cpvt IS NOT NULL) v),

     p_pos_interval_histogram AS (SELECT jsonb_agg(h) AS histogram
                                  FROM (WITH n_bins AS (SELECT 50 AS n),
                                             ranges
                                                 AS (SELECT MIN(lower(p_pos_interval))     AS min_val,
                                                            MAX(upper(p_pos_interval)) + 1 AS max_val
                                                     FROM variant_view_mv),
                                             bins
                                                 AS (SELECT generate_series(1,
                                                                            (SELECT n
                                                                             FROM n_bins)
                                                            ) AS bin),
                                             histogram
                                                 AS (SELECT width_bucket(
                                                                    lower(p_pos_interval),
                                                                    min_val,
                                                                    max_val,
                                                                    (SELECT n
                                                                     FROM n_bins)
                                                            )                 AS bin,
                                                            COUNT(variant_id) AS freq
                                                     FROM variant_view_mv,
                                                          ranges
                                                     WHERE variant_view_mv.num_individuals >= 1
                                                     GROUP BY bin)
                                        SELECT bins.bin,
                                               COALESCE(histogram.freq, 0) AS freq
                                        FROM bins
                                                 LEFT JOIN
                                             histogram ON bins.bin = histogram.bin
                                        ORDER BY bins.bin) h),
     p_pos_interval
         AS (SELECT build_ui_filter(jsonb_agg(p), 'range', 'pPosInterval',
                                    'Protein Change Position', 6,
                                    (SELECT histogram
                                     FROM p_pos_interval_histogram),
                                    description := 'The position(s) of the amino acid(s) affected by the variant.'
                    ) AS p_pos_interval
             FROM (SELECT MIN(lower(p_pos_interval))     AS min,
                          MAX(upper(p_pos_interval)) - 1 AS max
                   FROM variant_view_mv
                   WHERE p_pos_interval IS NOT NULL) AS p),

     -- structure domains
     structure_domain AS (SELECT build_ui_filter(jsonb_agg(s), 'combobox',
                                                 'structureDomain',
                                                 'Protein Domains Affected',
                                                 7,
                                                 description := 'Filter for variants affecting specific protein domains.',
                                                 shortlabel := 'domains'
                                 ) AS structure_domain

                          FROM (SELECT DISTINCT structure_id AS value,
                                                CASE
                                                    WHEN symbol IS NULL
                                                        THEN name
                                                    ELSE name || ' (' || symbol || ')'
                                                    END      AS label
                                FROM structure) AS s),

     exon_range_histogram AS (SELECT jsonb_agg(h) AS histogram
                              FROM (WITH ranges
                                             AS (SELECT MIN(lower(exons))     AS min_val,
                                                        MAX(lower(exons)) + 1 AS max_val
                                                 FROM variant_view_mv),
                                         bins
                                             AS (SELECT generate_series(1, 105) AS bin),
                                         histogram
                                             AS (SELECT width_bucket(
                                                                lower(exons),
                                                                min_val,
                                                                max_val,
                                                                105)      AS bin,
                                                        COUNT(variant_id) AS freq
                                                 FROM variant_view_mv,
                                                      ranges
                                                 WHERE variant_view_mv.num_individuals >= 1
                                                 GROUP BY bin)
                                    SELECT bins.bin,
                                           COALESCE(histogram.freq, 0) AS freq
                                    FROM bins
                                             LEFT JOIN
                                         histogram ON bins.bin = histogram.bin
                                    ORDER BY bins.bin) h),
     -- exons (RANGE INPUT)
     exon_range
         AS (SELECT build_ui_filter(jsonb_agg(e), 'range', 'exonRange',
                                    'Exons Affected (Range)', 8,
                                    (SELECT histogram
                                     FROM exon_range_histogram)) AS exon_range

             FROM (SELECT MIN(lower(exons))     AS min,
                          MAX(upper(exons)) - 1 AS max
                   FROM variant_view_mv) e),

     exon AS (SELECT build_ui_filter(jsonb_agg(e), 'combobox', 'exons',
                                     'Exons Affected', 9,
                                     shortlabel := 'exons') AS exon

              FROM (SELECT DISTINCT lower(exons)            AS value,
                                    'Exon ' || lower(exons) AS label
                    FROM variant_view_mv
                    WHERE exons IS NOT NULL
                    ORDER BY value) e),

     clinvar_conditions AS (SELECT build_ui_filter(jsonb_agg(c), 'combobox',
                                                   'clinvarConditions',
                                                   'Disease Association (ClinVar)',
                                                   10,
                                                   description := 'Filter for variants associated with a disease in ClinVar.',
                                                   shortlabel := 'diseases') AS clinvar_conditions

                            FROM (SELECT DISTINCT c.condition_id AS value,
                                                  c.condition    AS label,
                                                  jsonb_agg(
                                                          DISTINCT cs.synonym
                                                  )              AS alt_labels

                                  FROM variant
                                           JOIN clinvar_variant_linked_condition AS cvlc
                                                ON variant.variant_id = cvlc.variant_id
                                           JOIN condition AS c
                                                ON cvlc.condition_id = c.condition_id
                                           LEFT JOIN public.condition_synonym cs
                                                     on c.condition_id = cs.condition_id
                                  GROUP BY c.condition_id, condition
                                  ORDER BY condition) AS c),

     variant_to_individuals AS (SELECT v.variant_id, iv.individual_id
                                FROM variant v
                                         JOIN individual_variant iv
                                              ON iv.variant_id = v.variant_id),


     individual_conditions
         AS (SELECT build_ui_filter(jsonb_agg(c), 'combobox',
                                    'individualConditions',
                                    'Individuals with Disease',
                                    11, null, true,
                                    description := 'Filter for variants associated with patients with a recorded disease.',
                                    shortlabel := 'diseases') AS individual_conditions
             FROM (SELECT DISTINCT c.condition_id AS value,
                                   condition      AS label,
                                   jsonb_agg(
                                           DISTINCT
                                           cs.synonym
                                   )              AS alt_labels
                   FROM variant_to_individuals AS vi
                            JOIN individual_condition AS ic
                                 ON vi.individual_id = ic.individual_id
                            JOIN condition AS c
                                 ON ic.condition_id = c.condition_id
                            LEFT JOIN public.condition_synonym cs
                                      on c.condition_id = cs.condition_id
                   GROUP BY c.condition_id, condition
                   ORDER BY condition) AS c),
     individual_treatments
         AS (SELECT build_ui_filter(jsonb_agg(t), 'combobox',
                                    'individualTreatments',
                                    'Individuals with Treatment',
                                    12, null, true,
                                    description := 'Filter for variants associated with patients with a recorded treatment.',
                                    shortlabel := 'treatments') AS individual_treatments

             FROM (SELECT DISTINCT t.treatment_id   AS value,
                                   t.treatment_name AS label
                   FROM variant_to_individuals AS vi
                            JOIN treatment_record AS tr
                                 ON vi.individual_id = tr.patient_id
                            JOIN treatment AS t
                                 ON tr.treatment_id = t.treatment_id
                   ORDER BY treatment_name) AS t),

     -- subtract 1 from range types since they are non-inclusive


     c_pos_interval
         AS (SELECT build_ui_filter(jsonb_agg(c), 'range', 'cPosInterval',
                                    'cDNA Change Position',
                                    13, null, true,
                                    description := 'The position(s) of the nucleotide(s) affected by the variant.'
                    ) AS c_pos_interval

             FROM (SELECT MIN(lower(c_pos_interval))     AS min,
                          MAX(upper(c_pos_interval)) - 1 AS max
                   FROM variant_view_mv
                   WHERE c_pos_interval IS NOT NULL) AS c),

     g_pos_interval
         AS (SELECT build_ui_filter(jsonb_agg(g), 'range', 'gPosInterval',
                                    'Genomic Change Position',
                                    14, null, true,
                                    description := 'The position(s) of the nucleotide(s) affected by the variant.'
                    ) AS g_pos_interval

             FROM (SELECT MIN(lower(g_pos_interval))     AS min,
                          MAX(upper(g_pos_interval)) - 1 AS max
                   FROM variant_view_mv
                   WHERE g_pos_interval IS NOT NULL) AS g),


-- make it into 1 row
     row_result AS (SELECT *
                    FROM provenance,
                         num_individuals,
                         avg_age_of_onset_cpvt,
                         clinical_significance,
                         clinvar_conditions,
                         individual_conditions,
                         individual_treatments,
                         p_pos_interval,
                         structure_domain,
                         exon_range,
                         exon,
                         edit_type,
                         g_pos_interval,
                         c_pos_interval)
        ,
     json_values AS (SELECT jsonb_agg(value) AS result
                     FROM row_result, jsonb_each(row_to_json(row_result.*)::jsonb))
INSERT
INTO kv_store (key, value)
SELECT 'filters:variants', result
FROM json_values
RETURNING *;



