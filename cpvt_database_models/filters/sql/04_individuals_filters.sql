DELETE
FROM kv_store
WHERE key = 'filters:individuals';

--- NEW STATEMENT

WITH
    -- PUBLICATION
    publication_year_histogram AS (SELECT jsonb_agg(h) AS histogram
                                   FROM (WITH n_bins AS (SELECT 30 AS n),
                                              ranges
                                                  AS (SELECT MIN(publication_year) AS min_val,
                                                             MAX(publication_year) AS max_val
                                                      FROM individuals_mv),
                                              bins
                                                  AS (SELECT generate_series(1, (SELECT n FROM n_bins)) AS bin),
                                              histogram
                                                  AS (SELECT width_bucket(
                                                                     publication_year,
                                                                     min_val,
                                                                     max_val +
                                                                     1,
                                                                     (SELECT n FROM n_bins)) AS bin,
                                                             COUNT(publication_id)           AS freq
                                                      FROM individuals_mv,
                                                           ranges
                                                      GROUP BY bin)
                                         SELECT bins.bin,
                                                COALESCE(histogram.freq, 0) AS freq
                                         FROM bins
                                                  LEFT JOIN histogram ON bins.bin = histogram.bin
                                         ORDER BY bins.bin) h),
    publication_year AS (SELECT build_ui_filter(
                                        jsonb_agg(p), 'range',
                                        'publicationYear', 'Publication Year',
                                        1, (SELECT histogram
                                            FROM publication_year_histogram),
                                        description := 'The year the patient was published in an article.'
                                )
                                    AS publication_year
                         FROM (SELECT MIN(publication_year) AS min,
                                      MAX(publication_year) AS max
                               FROM individuals_mv) p),

    -- DEMOGRAPHICS
    sex AS (SELECT build_ui_filter(jsonb_agg(s), 'checkboxes', 'sex', 'Sex', 2)
                       AS sex
            FROM (SELECT isx.individual_sex_id AS value,
                         isx.value             AS label
                  FROM individual_sex isx) AS s),

    -- CONDITIONS
    individuals_cpvt AS (SELECT individual_id,
                                age_of_onset
                         FROM individual_condition AS ic
                                  JOIN condition AS c
                                       ON ic.condition_id = c.condition_id
                                  LEFT JOIN public.condition_synonym cs
                                            on c.condition_id = cs.condition_id
                         WHERE ic.has_condition = TRUE
                           AND c.condition LIKE
                               'Catecholaminergic polymorphic ventricular tachycardia%'),
    cpvt_age_of_onset_histogram AS (SELECT jsonb_agg(h) AS histogram
                                    FROM (WITH n_bins AS (SELECT 30 AS n),
                                               ranges
                                                   AS (SELECT MIN(age_of_onset) AS min_val,
                                                              MAX(age_of_onset) AS max_val
                                                       FROM individuals_cpvt AS ic),
                                               bins
                                                   AS (SELECT generate_series(1, (SELECT n FROM n_bins)) AS bin),
                                               histogram
                                                   AS (SELECT width_bucket(
                                                                      age_of_onset,
                                                                      min_val,
                                                                      max_val +
                                                                      1,
                                                                      (SELECT n FROM n_bins)) AS bin,
                                                              COUNT(individual_id)            AS freq
                                                       FROM individuals_cpvt,
                                                            ranges
                                                       GROUP BY bin)
                                          SELECT bins.bin,
                                                 COALESCE(histogram.freq, 0) AS freq
                                          FROM bins
                                                   LEFT JOIN histogram ON bins.bin = histogram.bin
                                          ORDER BY bins.bin) h),
    cpvt_age_of_onset
        AS (SELECT build_ui_filter(jsonb_agg(a), 'range', 'cpvtAgeOfOnset',
                                   'CPVT Age of Onset', 3,
                                   (SELECT histogram
                                    FROM cpvt_age_of_onset_histogram),
                                   description := 'The age at which the patient was diagnosed with Catecholaminergic Polymorphic Ventricular Tachycardia (CPVT).'
                   )
                       AS avg_age_of_onset_cpvt
            FROM (SELECT MIN(age_of_onset) AS min, MAX(age_of_onset) AS max
                  FROM individuals_cpvt) AS a),

    individual_conditions_has
        AS (SELECT build_ui_filter(jsonb_agg(c), 'combobox',
                                   'hasCondition',
                                   'With Condition',
                                   4,
                                   histogram := NULL,
                                   shortlabel := 'disease',
                                   description := 'Filter for patients diagnosed with a specific condition in a publication.',
                                   hidden := TRUE
                   ) AS individual_conditions_has
            FROM (SELECT DISTINCT c.condition_id AS value,
                                  condition      AS label,
                                  jsonb_agg(
                                          DISTINCT
                                          cs.synonym
                                  )              AS alt_labels
                  FROM individual_condition AS ic
                           JOIN condition AS c
                                ON ic.condition_id = c.condition_id
                           LEFT JOIN public.condition_synonym cs
                                     on c.condition_id = cs.condition_id
                  WHERE ic.has_condition = TRUE
                  GROUP BY c.condition_id, condition
                  ORDER BY condition) AS c),
    individual_conditions_no
        AS (SELECT build_ui_filter(jsonb_agg(c), 'combobox',
                                   'noCondition',
                                   'Without Condition',
                                   5, hidden := TRUE,
                                   shortlabel := 'disease',
                                   description :=
                                       'Filter for patients not reported to have a specific condition in a publication. ' ||
                                       'This filter will also exclude patients that have not had the condition reported.'
                   ) AS individual_conditions_not_has
            FROM (SELECT DISTINCT c.condition_id AS value,
                                  condition      AS label,
                                  jsonb_agg(
                                          DISTINCT
                                          cs.synonym
                                  )              AS alt_labels
                  FROM individual_condition AS ic
                           JOIN condition AS c
                                ON ic.condition_id = c.condition_id
                           LEFT JOIN public.condition_synonym cs
                                     on c.condition_id = cs.condition_id
                  WHERE ic.has_condition = FALSE
                  GROUP BY c.condition_id, condition
                  ORDER BY condition) AS c),

-- FAMILY HISTORY
    fam_history_scd AS (SELECT family_history_record_id,
                               num_family_members
                        FROM family_history_record
                                 JOIN condition
                                      ON family_history_record.condition_id =
                                         condition.condition_id
                        WHERE condition.condition LIKE 'Sudden cardiac death%'),
    fam_history_scd_histogram AS (SELECT jsonb_agg(h) AS histogram
                                  FROM (WITH n_bins AS (SELECT 30 AS n),
                                             ranges
                                                 AS (SELECT MIN(num_family_members) AS min_val,
                                                            MAX(num_family_members) AS max_val
                                                     FROM fam_history_scd),
                                             bins
                                                 AS (SELECT generate_series(1, (SELECT n FROM n_bins)) AS bin),
                                             histogram AS (SELECT width_bucket(
                                                                          num_family_members,
                                                                          min_val,
                                                                          max_val +
                                                                          1,
                                                                          (SELECT n FROM n_bins)) AS bin,
                                                                  COUNT(family_history_record_id) AS freq
                                                           FROM fam_history_scd,
                                                                ranges
                                                           GROUP BY bin)
                                        SELECT bins.bin,
                                               COALESCE(histogram.freq, 0) AS freq
                                        FROM bins
                                                 LEFT JOIN histogram ON bins.bin = histogram.bin
                                        ORDER BY bins.bin) h),
    fam_history_scd_num_family_members AS (SELECT build_ui_filter(
                                                          jsonb_agg(a),
                                                          'range',
                                                          'numFamilyMembersScd',
                                                          'Num Family Members with SCD',
                                                          6,
                                                          (SELECT histogram
                                                           FROM fam_history_scd_histogram),
                                                          hidden := TRUE,
                                                          description :=
                                                              'The number of family members with a history of sudden cardiac death (SCD).'
                                                  ) AS num_family_members_scd
                                           FROM (SELECT MIN(num_family_members) AS min,
                                                        MAX(num_family_members) AS max
                                                 FROM fam_history_scd) a),
    mother_has_scd AS (SELECT build_ui_filter(
                                      jsonb_build_array(
                                              jsonb_build_object('value',
                                                                 1,
                                                                 'label',
                                                                 'Yes'),
                                              jsonb_build_object('value',
                                                                 0,
                                                                 'label', 'No')
                                      )
                                  , 'checkboxes', 'motherHasScd',
                                      'Mother Has Sudden Cardiac Death',
                                      7,
                                      hidden := TRUE
                              ) AS mother_has_scd),
    father_has_scd AS (SELECT build_ui_filter(
                                      jsonb_build_array(
                                              jsonb_build_object('value',
                                                                 1,
                                                                 'label',
                                                                 'Yes'),
                                              jsonb_build_object('value',
                                                                 0,
                                                                 'label', 'No')
                                      ), 'checkboxes', 'fatherHasScd',
                                      'Father Has Sudden Cardiac Death',
                                      8, hidden := TRUE) AS father_has_scd),

    -- TREATMENTS
    individual_treatments
        AS (SELECT build_ui_filter(jsonb_agg(t), 'combobox',
                                   'individualTreatments',
                                   'Treatments Received',
                                   9, null,
                                   hidden := TRUE,
                                   shortlabel := 'treatments',
                                   description := 'Filter for patients that have received a specific treatment.'
                   ) AS individual_treatments

            FROM (SELECT DISTINCT t.treatment_id   AS value,
                                  t.treatment_name AS label
                  FROM treatment_record AS tr
                           JOIN treatment AS t
                                ON tr.treatment_id = t.treatment_id
                  ORDER BY treatment_name) AS t),


    -- INDIVIDUAL VARIANT
    edit_type
        AS (SELECT build_ui_filter(jsonb_agg(e), 'checkboxes', 'editType',
                                   'Consequence Type', 10,
                                   description := 'The consequence of a patient'' variant to the genome or protein sequence.'
                   ) AS edit_type

            FROM (SELECT DISTINCT edit_type_id AS value,
                                  name         AS label
                  FROM edit_type) AS e),

    zygosity AS (SELECT build_ui_filter(jsonb_agg(z), 'checkboxes', 'zygosity',
                                        'Zygosity', 11,
                                        description := 'The zygosity of the variant in the patient'
                        ) AS zygosity

                 FROM (SELECT DISTINCT zygosity_id AS value,
                                       zygosity    AS label
                       FROM zygosity) AS z),

    inheritance
        AS (SELECT build_ui_filter(jsonb_agg(i), 'checkboxes', 'inheritance',
                                   'Inheritance', 12,
                                   description := 'The inheritance pattern of the variant in the patient'
                   ) AS inheritance

            FROM (SELECT DISTINCT vi.variant_inheritance_id AS value,
                                  vi.variant_inheritance    AS label
                  FROM variant_inheritance vi) AS i),


    p_pos_interval_histogram AS (SELECT jsonb_agg(h) AS histogram
                                 FROM (WITH n_bins AS (SELECT 50 AS n),
                                            ranges
                                                AS (SELECT MIN(p_pos_start)     AS min_val,
                                                           MAX(p_pos_start) + 1 AS max_val
                                                    FROM individuals_mv),
                                            bins
                                                AS (SELECT generate_series(1,
                                                                           (SELECT n
                                                                            FROM n_bins)
                                                           ) AS bin),
                                            histogram
                                                AS (SELECT width_bucket(
                                                                   p_pos_start,
                                                                   min_val,
                                                                   max_val,
                                                                   (SELECT n
                                                                    FROM n_bins)
                                                           )                    AS bin,
                                                           COUNT(individual_id) AS freq
                                                    FROM individuals_mv,
                                                         ranges
                                                    GROUP BY bin)
                                       SELECT bins.bin,
                                              COALESCE(histogram.freq, 0) AS freq
                                       FROM bins
                                                LEFT JOIN
                                            histogram ON bins.bin = histogram.bin
                                       ORDER BY bins.bin) h),
    p_pos_interval
        AS (SELECT build_ui_filter(jsonb_agg(p), 'range', 'pPosInterval',
                                   'Variant Protein Change Position', 13,
                                   (SELECT histogram
                                    FROM p_pos_interval_histogram),
                                   description := 'The position(s) of the amino acid(s) affected by the variant.'
                   ) AS p_pos_interval
            FROM (SELECT MIN(p_pos_start)     AS min,
                         MAX(p_pos_start) - 1 AS max
                  FROM individuals_mv) AS p),

    structure_domain AS (SELECT build_ui_filter(jsonb_agg(s), 'combobox',
                                                'structureDomain',
                                                'Variant Protein Domains Affected',
                                                14,
                                                shortlabel := 'domains',
                                                description := 'Filter for patients with variants that affect a specific protein domain.'
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
                                            AS (SELECT MIN(exon_start)     AS min_val,
                                                       MAX(exon_start) + 1 AS max_val
                                                FROM individuals_mv),
                                        bins
                                            AS (SELECT generate_series(1, 105) AS bin),
                                        histogram
                                            AS (SELECT width_bucket(
                                                               exon_start,
                                                               min_val,
                                                               max_val,
                                                               105)         AS bin,
                                                       COUNT(individual_id) AS freq
                                                FROM individuals_mv,
                                                     ranges
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
                                   'Variant Exons Affected (Range)', 15,
                                   (SELECT histogram
                                    FROM exon_range_histogram),
                                   true
                   ) AS exon_range

            FROM (SELECT MIN(exon_start)   AS min,
                         MAX(exon_end) - 1 AS max
                  FROM individuals_mv) e),

    exon AS (SELECT build_ui_filter(jsonb_agg(e), 'combobox', 'exons',
                                    'Variant Exons Affected', 16, null,
                                    true, shortlabel := 'exons') AS exon

             FROM (SELECT DISTINCT exon_start            AS value,
                                   'Exon ' || exon_start AS label
                   FROM individuals_mv
                   WHERE exon_start IS NOT NULL
                   ORDER BY value) e),


-- make it into 1 row
    row_result AS (SELECT *
                   FROM sex,
                        publication_year,
                        cpvt_age_of_onset,
                        individual_conditions_has,
                        individual_conditions_no,
                        fam_history_scd_num_family_members,
                        mother_has_scd,
                        father_has_scd,
                        individual_treatments,
                        edit_type,
                        zygosity,
                        inheritance,
                        p_pos_interval,
                        structure_domain,
                        exon_range,
                        exon)
        ,
    json_values AS (SELECT jsonb_agg(value) AS result
                    FROM row_result, jsonb_each(row_to_json(row_result.*)::jsonb))
INSERT
INTO kv_store (key, value)
SELECT 'filters:individuals', result
FROM json_values
RETURNING *;



