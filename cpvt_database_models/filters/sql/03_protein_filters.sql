DELETE
FROM kv_store
WHERE key = 'filters:proteins';

--- NEW STATEMENT

WITH provenance_ids AS (SELECT i -> 'dataset'    AS label,
                               i -> 'dataset_id' AS value
                        FROM (SELECT jsonb_array_elements(provenance) AS i
                              FROM protein_consequence_mv pcm) i),
     provenance
         AS (SELECT build_ui_filter(jsonb_agg(DISTINCT provenance_ids),
                                    'checkboxes',
                                    'provenance',
                                    'Provenance', 1) AS provenance
             FROM provenance_ids),

     edit_type
         AS (SELECT build_ui_filter(jsonb_agg(e), 'checkboxes', 'editType',
                                    'Consequence Type', 2,
                                    description := 'The consequence of a variant on the protein sequence.'
                    ) AS edit_type

             FROM (SELECT DISTINCT edit_type_id AS value,
                                   name         AS label
                   FROM edit_type) AS e),

     clinical_significance_ids AS (SELECT i -> 'clinical_significance'    AS label,
                                          i -> 'clinical_significance_id' AS value
                                   FROM (SELECT jsonb_array_elements(variant_info) AS i
                                         FROM protein_consequence_mv pcm) i),
     clinical_significance
         AS (SELECT build_ui_filter(
                            jsonb_agg(DISTINCT clinical_significance_ids),
                            'checkboxes',
                            'clinicalSignificance',
                            'Clinical Significance', 3,
                            description :=
                                'The clinical significance of a variant is a classification of the variant ' ||
                                'based on its potential impact on health calculated by the NCBI in the ClinVar database.'
                    ) clinical_significance
             FROM clinical_significance_ids),

     num_individuals_hist AS (SELECT jsonb_agg(h) AS histogram
                              FROM (WITH ranges
                                             AS (SELECT MIN(num_individuals) AS min_val,
                                                        MAX(num_individuals) AS max_val
                                                 FROM protein_consequence_mv),
                                         bins
                                             AS (SELECT generate_series(1, 25) AS bin),
                                         histogram
                                             AS (SELECT width_bucket(
                                                                num_individuals,
                                                                min_val + 1,
                                                                max_val + 1,
                                                                25) AS bin,
                                                        ROUND(
                                                                LOG(COUNT(p_hgvs_string) + 1)::numeric,
                                                                2)  AS freq
                                                 FROM protein_consequence_mv,
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
                                     FROM num_individuals_hist)) AS num_individuals
             FROM (SELECT MAX(num_individuals) AS max,
                          MIN(num_individuals) AS min
                   FROM protein_consequence_mv) v),

     p_pos_interval_histogram AS (SELECT jsonb_agg(h) AS histogram
                                  FROM (WITH n_bins AS (SELECT 50 AS n),
                                             ranges
                                                 AS (SELECT MIN(lower(p_pos_interval))     AS min_val,
                                                            MAX(upper(p_pos_interval)) + 1 AS max_val
                                                     FROM protein_consequence_mv),
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
                                                            )                    AS bin,
                                                            COUNT(p_hgvs_string) AS freq
                                                     FROM protein_consequence_mv,
                                                          ranges
                                                     WHERE protein_consequence_mv.num_individuals >= 1
                                                     GROUP BY bin)
                                        SELECT bins.bin,
                                               COALESCE(histogram.freq, 0) AS freq
                                        FROM bins
                                                 LEFT JOIN
                                             histogram ON bins.bin = histogram.bin
                                        ORDER BY bins.bin) h),

     p_pos_interval
         AS (SELECT build_ui_filter(jsonb_agg(p), 'range', 'pPosInterval',
                                    'Protein Change Position', 5,
                                    (SELECT histogram
                                     FROM p_pos_interval_histogram),
                                    description := 'The position(s) of the amino acid(s) affected by the variant.'
                    ) AS p_pos_interval
             FROM (SELECT MIN(lower(p_pos_interval))     AS min,
                          MAX(upper(p_pos_interval)) - 1 AS max
                   FROM protein_consequence_mv
                   WHERE p_pos_interval IS NOT NULL) AS p),

     structure_domain AS (SELECT build_ui_filter(jsonb_agg(s), 'combobox',
                                                 'structureDomain',
                                                 'Protein Domains Affected',
                                                 6, shortlabel := 'domains',
                                                 description := 'Filter for variants affecting specific protein domains.'
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
                                             AS (SELECT MIN(exon_start)   AS min_val,
                                                        MAX(exon_end) + 1 AS max_val
                                                 FROM protein_consequence_mv),
                                         bins
                                             AS (SELECT generate_series(1, 105) AS bin),
                                         histogram
                                             AS (SELECT width_bucket(
                                                                exon_start,
                                                                min_val,
                                                                max_val,
                                                                105)         AS bin,
                                                        COUNT(p_hgvs_string) AS freq
                                                 FROM protein_consequence_mv,
                                                      ranges
                                                 WHERE protein_consequence_mv.num_individuals >= 1
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
                                    'Exons Affected (Range)',
                                    7, (SELECT histogram
                                        FROM exon_range_histogram)) AS exon_range

             FROM (SELECT MIN(exon_start)   AS min,
                          MAX(exon_end) - 1 AS max
                   FROM protein_consequence_mv) e),
     exon AS (SELECT build_ui_filter(jsonb_agg(e), 'combobox', 'exons',
                                     'Exons Affected', 8,
                                     shortlabel := 'exons') AS exon

              FROM (SELECT DISTINCT exon_start            AS value,
                                    'Exon ' || exon_start AS label
                    FROM protein_consequence_mv
                    WHERE exon_start IS NOT NULL
                    ORDER BY value) e),
     clinvar_condition_ids AS (SELECT i -> 'condition'    AS label,
                                      i -> 'condition_id' AS value
                               FROM (SELECT jsonb_array_elements(clinvar_conditions) AS i
                                     FROM protein_consequence_mv pcm) i),
     clinvar_conditions
         AS (SELECT build_ui_filter(jsonb_agg(DISTINCT clinvar_condition_ids),
                                    'combobox', 'clinvarConditions',
                                    'Disease Association (ClinVar)',
                                    9,
                                    description := 'Filter for variants associated with a disease in ClinVar.',
                                    shortlabel := 'diseases') AS clinvar_conditions
             FROM clinvar_condition_ids),

     individual_conditions_ids AS (SELECT i -> 'condition'    AS label,
                                          i -> 'condition_id' AS value
                                   FROM (SELECT jsonb_array_elements(individual_conditions) AS i
                                         FROM protein_consequence_mv pcm) i),
     individual_conditions
         AS (SELECT build_ui_filter(
                            jsonb_agg(DISTINCT individual_conditions_ids),
                            'combobox', 'individualConditions',
                            'Individuals with Disease',
                            10, null, true,
                            description := 'Filter for variants associated with patients with a recorded disease.',
                            shortlabel := 'diseases') AS individual_conditions
             FROM individual_conditions_ids),

     individual_treatments_ids AS (SELECT i -> 'treatment'    AS label,
                                          i -> 'treatment_id' AS value
                                   FROM (SELECT jsonb_array_elements(individual_treatments) AS i
                                         FROM protein_consequence_mv pcm) i),
     individual_treatments
         AS (SELECT build_ui_filter(
                            jsonb_agg(DISTINCT individual_treatments_ids),
                            'checkboxes', 'individualTreatments',
                            'Individuals with Treatment',
                            11, null, true,
                            description := 'Filter for variants associated with patients with a recorded treatment.',
                            shortlabel := 'treatments') AS individual_treatments
             FROM individual_treatments_ids),


     row_result AS (SELECT *
                    FROM provenance,
                         num_individuals,
                         clinical_significance,
                         structure_domain,
                         edit_type,
                         clinvar_conditions,
                         individual_conditions,
                         individual_treatments,
                         p_pos_interval,
                         exon_range,
                         exon),
     json_values AS (SELECT jsonb_agg(value) AS result
                     FROM row_result, jsonb_each(row_to_json(row_result.*)::jsonb))
INSERT
INTO kv_store (key, value)
SELECT 'filters:proteins', result
FROM json_values
RETURNING *;
