DROP MATERIALIZED VIEW IF EXISTS individuals_mv CASCADE;
-- Document view
CREATE MATERIALIZED VIEW individuals_mv AS
WITH ranked_variants AS (SELECT i.individual_id,
                                iv.variant_id,
                                ROW_NUMBER()
                                OVER (PARTITION BY i.individual_id ORDER BY iv.variant_id) AS variant_rank
                         FROM individual i
                                  JOIN individual_variant iv
                                       ON i.individual_id = iv.individual_id),
     iv_one_to_many AS (
         -- collaspe into a many to one relationship
         SELECT iv.individual_id,
                iv.variant_id
         FROM ranked_variants iv
         WHERE iv.variant_rank = 1),
     ranked_publications AS (SELECT i.individual_id,
                                    p.publication_id,
                                    ROW_NUMBER()
                                    OVER (PARTITION BY i.individual_id ORDER BY p.year) AS publication_rank
                             FROM individual i
                                      JOIN individual_to_publication ip
                                           ON i.individual_id = ip.individual_id
                                      JOIN publication p
                                           ON ip.publication_id = p.publication_id),
     first_pub_per_individual AS (SELECT rp.individual_id,
                                         rp.publication_id,
                                         p.title        AS publication_title,
                                         p.year         AS publication_year,
                                         p.first_author AS publication_first_author,
                                         p.reference    AS publication_reference,
                                         p.doi          AS publication_doi
                                  FROM ranked_publications rp
                                           JOIN publication p
                                                ON rp.publication_id = p.publication_id
                                  WHERE rp.publication_rank = 1),
     indiv_treatment AS (SELECT i.individual_id,
                                jsonb_agg(jsonb_build_object(
                                        'treatment_id',
                                        t.treatment_id,
                                        'treatment',
                                        t.treatment_name,
                                        'treatment_taken',
                                        tr.treatment_taken,
                                        'treatment_effective',
                                        tr.effective
                                          )) AS individual_treatments
                         FROM individual i
                                  JOIN treatment_record tr
                                       ON i.individual_id = tr.patient_id
                                  JOIN treatment t
                                       ON tr.treatment_id = t.treatment_id
                         GROUP BY i.individual_id),
     indiv_condition AS (SELECT i.individual_id,
                                jsonb_agg(DISTINCT
                                          jsonb_build_object(
                                                  'condition_id',
                                                  c.condition_id,
                                                  'condition',
                                                  c.condition,
                                                  'has_condition',
                                                  ic.has_condition,
                                                  'age_of_onset',
                                                  ic.age_of_onset,
                                                  'age_of_presentation',
                                                  ic.age_of_presentation,
                                                  'onset_symptoms',
                                                  ic.onset_symptoms,
                                                  'description',
                                                  ic.description
                                          )) AS individual_conditions
                         FROM individual i
                                  JOIN individual_condition ic
                                       ON i.individual_id = ic.individual_id
                                  JOIN condition c
                                       ON ic.condition_id = c.condition_id
                         GROUP BY i.individual_id),
     family_history_members AS (SELECT fhr.family_history_record_id,
                                       jsonb_agg(
                                               DISTINCT jsonb_build_object(
                                               'family_member_id',
                                               fmh.kinship_name_id,
                                               'kinship_name',
                                               kn.name,
                                               'has_condition',
                                               fmh.has_condition
                                                        )
                                       ) AS family_members
                                FROM family_history_record fhr
                                         JOIN family_member_history fmh
                                              ON fhr.family_history_record_id =
                                                 fmh.family_history_record_id
                                         JOIN kinship_name kn
                                              ON fmh.kinship_name_id = kn.kinship_name_id
                                GROUP BY fhr.family_history_record_id),
     family_history AS (SELECT fhr.individual_id,
                               jsonb_agg(
                                       DISTINCT jsonb_build_object(
                                       'condition_id',
                                       c.condition_id,
                                       'condition',
                                       c.condition,
                                       'num_family_members',
                                       fhr.num_family_members,
                                       'family_members',
                                       fm.family_members
                                                )
                               ) AS family_history

                        FROM family_history_record fhr
                                 JOIN condition c
                                      ON fhr.condition_id = c.condition_id
                                 LEFT JOIN family_history_members fm
                                           ON fhr.family_history_record_id =
                                              fm.family_history_record_id
                        GROUP BY fhr.family_history_record_id),
     variant_info AS (SELECT i.individual_id,
                             vv.variant_id,
                             vv.hgvs_string,
                             vv.clinvar_variation_id,
                             vv.clinical_significance_id,
                             vv.clinical_significance,
                             vv.sequence_variant_id,
                             vv.g_reference_sequence,
                             vv.g_edit_type_id,
                             vv.g_edit_type,
                             vv.g_posedit_str,
                             LOWER(vv.g_pos_interval) AS g_pos_start,
                             UPPER(vv.g_pos_interval) AS g_pos_end,
                             vv.g_edit_ref,
                             vv.g_edit_alt,
                             vv.g_hgvs_string,
                             vv.c_reference_sequence,
                             vv.c_edit_type_id,
                             vv.c_edit_type,
                             vv.c_posedit_str,
                             LOWER(vv.c_pos_interval) AS c_pos_start,
                             UPPER(vv.c_pos_interval) AS c_pos_end,
--                              vv.c_pos_interval,
                             vv.c_start_offset,
                             vv.c_end_offset,
                             vv.c_edit_ref,
                             vv.c_edit_alt,
                             vv.c_hgvs_string,
                             vv.gene_symbol,
                             vv.p_reference_sequence,
                             vv.p_edit_type_id,
                             vv.p_edit_type,
                             vv.p_posedit_str,
                             vv.p_posedit_aa1,
                             vv.p_posedit_aa3,
                             LOWER(vv.p_pos_interval) AS p_pos_start,
                             UPPER(vv.p_pos_interval) AS p_pos_end,
--                              vv.p_pos_interval,
                             vv.p_start_aa,
                             vv.p_end_aa,
                             vv.p_edit_ref,
                             vv.p_edit_alt,
                             vv.p_hgvs_string,
                             LOWER(vv.exons)          AS exon_start,
                             UPPER(vv.exons)          AS exon_end,
                             vv.structure_domains
                      FROM iv_one_to_many i
                               JOIN variant_view_mv vv
                                    ON i.variant_id = vv.variant_id)
-- SELECT *
-- FROM ip_one_to_many;
SELECT i.individual_id,
       isx.individual_sex_id,
       isx.value AS sex,
       ivt.zygosity_id,
       z.zygosity,
       ivt.variant_inheritance_id,
       vi.variant_inheritance,
       fppi.publication_id,
       fppi.publication_title,
       fppi.publication_year,
       fppi.publication_first_author,
       fppi.publication_reference,
       fppi.publication_doi,
       it.individual_treatments,
       ic.individual_conditions,
       fh.family_history,
       vif.variant_id,
       hgvs_string,
       clinvar_variation_id,
       clinical_significance_id,
       clinical_significance,
       sequence_variant_id,
       g_reference_sequence,
       g_edit_type_id,
       g_edit_type,
       g_posedit_str,
       g_pos_start,
       g_pos_end,
       g_edit_ref,
       g_edit_alt,
       g_hgvs_string,
       c_reference_sequence,
       c_edit_type_id,
       c_edit_type,
       c_posedit_str,
       c_pos_start,
       c_pos_end,
       c_start_offset,
       c_end_offset,
       c_edit_ref,
       c_edit_alt,
       c_hgvs_string,
       gene_symbol,
       p_reference_sequence,
       p_edit_type_id,
       p_edit_type,
       p_posedit_str,
       p_posedit_aa1,
       p_posedit_aa3,
       p_pos_start,
       p_pos_end,
       p_start_aa,
       p_end_aa,
       p_edit_ref,
       p_edit_alt,
       p_hgvs_string,
       exon_start,
       exon_end,
       structure_domains
FROM individual i
         LEFT JOIN individual_sex isx
                   ON i.individual_sex_id = isx.individual_sex_id
         LEFT JOIN variant_info vif
                   ON i.individual_id = vif.individual_id
         LEFT JOIN individual_variant ivt
                   ON i.individual_id = ivt.individual_id AND
                      vif.variant_id = ivt.variant_id
         LEFT JOIN zygosity z
                   ON z.zygosity_id = ivt.zygosity_id
         LEFT JOIN variant_inheritance vi
                   ON vi.variant_inheritance_id = ivt.variant_inheritance_id
         LEFT JOIN first_pub_per_individual fppi
                   ON i.individual_id = fppi.individual_id
         LEFT JOIN indiv_treatment it
                   ON i.individual_id = it.individual_id
         LEFT JOIN indiv_condition ic
                   ON i.individual_id = ic.individual_id
         LEFT JOIN family_history fh
                   ON i.individual_id = fh.individual_id
ORDER BY i.individual_id;

-- create the appropriate indexes for stuff we might want to join on or filter by
CREATE UNIQUE INDEX ON individuals_mv (individual_id);
CREATE INDEX ON individuals_mv (individual_sex_id);
CREATE INDEX ON individuals_mv (variant_id);
CREATE INDEX ON individuals_mv (zygosity_id);
CREATE INDEX ON individuals_mv (variant_inheritance_id);
CREATE INDEX ON individuals_mv (publication_id);
CREATE INDEX ON individuals_mv (publication_year);


-- variant info
CREATE INDEX ON individuals_mv (hgvs_string);
CREATE INDEX ON individuals_mv (clinvar_variation_id);
CREATE INDEX ON individuals_mv (clinical_significance_id);
CREATE INDEX ON individuals_mv (g_edit_type_id);
CREATE INDEX ON individuals_mv (c_edit_type_id);
CREATE INDEX ON individuals_mv (p_edit_type_id);
CREATE INDEX ON individuals_mv (g_pos_start);
CREATE INDEX ON individuals_mv (g_pos_end);
CREATE INDEX ON individuals_mv (c_pos_start);
CREATE INDEX ON individuals_mv (c_pos_end);
CREATE INDEX ON individuals_mv (p_pos_start);
CREATE INDEX ON individuals_mv (p_pos_end);
CREATE INDEX ON individuals_mv (exon_start);
CREATE INDEX ON individuals_mv (exon_end);

-- GIN index for jsonb columns
CREATE INDEX ON individuals_mv USING GIN (individual_treatments);
CREATE INDEX ON individuals_mv USING GIN (individual_conditions);
CREATE INDEX ON individuals_mv USING GIN (family_history);
CREATE INDEX ON individuals_mv USING GIN (structure_domains);
