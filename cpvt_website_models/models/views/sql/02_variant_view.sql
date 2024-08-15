-- c Variant to Exon
DROP VIEW IF EXISTS variant_to_exon_v CASCADE;
CREATE VIEW variant_to_exon_v AS
WITH seq_anno_to_exon AS (SELECT sa.seq_anno_id,
                                 e.start_i,
                                 e.end_i,
                                 e.ord + 1 AS exon_num,
                                 ex.alt_ac
                          FROM uta.seq_anno sa
                                   JOIN uta.transcript t ON sa.ac = t.ac
                                   JOIN uta.exon_set ex ON t.ac = ex.tx_ac
                                   JOIN uta.exon e ON ex.exon_set_id = e.exon_set_id),
     exon_ranges AS (SELECT sv.sequence_variant_id,
                            int4range(MIN(ex.exon_num),
                                      MAX(ex.exon_num), '[]') AS exons
                     FROM seq_anno_to_exon ex
                              JOIN sequence_variant sv
                                   ON ex.seq_anno_id = sv.c_reference_sequence_id
                              JOIN uta.seq_anno sa_g
                                   ON sv.g_reference_sequence_id = sa_g.seq_anno_id
                     WHERE sv.g_pos_interval && int4range(ex.start_i, ex.end_i)
                       AND sv.c_start_offset = 0
                       AND sv.c_end_offset = 0
                       AND sa_g.ac = ex.alt_ac
                     GROUP BY sv.sequence_variant_id)
SELECT *
FROM exon_ranges;


-- p variant to Structural domain(s)
DROP VIEW IF EXISTS p_variant_to_structure_v CASCADE;
CREATE VIEW p_variant_to_structure_v AS
SELECT sv.sequence_variant_id,
       s.structure_id,
       s.name,
       s.symbol
FROM sequence_variant sv
         JOIN structure_root_to_protein srtp
              ON sv.p_reference_sequence_id = srtp.protein_id
         JOIN structure_root sr
              ON srtp.structure_root_id = sr.structure_root_id
         JOIN structure s
              ON sr.structure_root_id = s.root_id
WHERE sv.p_pos_interval && s.residue_span
  AND s.parent_id IS NOT NULL;


-- Compute the average age of onset for each condition for each variant that
-- has an age of onset


-- Create a document view of the variant table
-- this is for easier querying of the variant table
-- including filters without having to join multiple tables
-- or using another document database
DROP MATERIALIZED VIEW IF EXISTS variant_view_mv CASCADE;
CREATE MATERIALIZED VIEW variant_view_mv AS
WITH
    -- VARIANT ORIGINS (clinvar or from review)
    variant_dataset AS (SELECT v.variant_id,
                               jsonb_agg(
                                       jsonb_build_object(
                                               'dataset_id', vd.dataset_id,
                                               'dataset', d.name
                                       )
                               ) AS provenance
                        FROM variant v
                                 JOIN variants_dataset_to_variant vd
                                      ON v.variant_id = vd.variant_id
                                 JOIN variants_dataset d
                                      ON vd.dataset_id = d.dataset_id
                        GROUP BY v.variant_id),
-- STRUCTURE
    structure_domains AS (SELECT pvs.sequence_variant_id,
                                 jsonb_agg(jsonb_build_object(
                                         'structure_id', pvs.structure_id,
                                         'structure_domain', pvs.name,
                                         'structure_domain_symbol', pvs.symbol
                                           )) AS structure_domains
                          FROM p_variant_to_structure_v pvs
                          GROUP BY pvs.sequence_variant_id),

-- CLINVAR CONDITIONS
    variant_conditions_clinvar AS (SELECT vc.variant_id,
                                          jsonb_agg(jsonb_build_object(
                                                  'condition_id',
                                                  c.condition_id,
                                                  'condition', c.condition
                                                    )) AS conditions
                                   FROM clinvar_variant_linked_condition vc
                                            JOIN condition c
                                                 ON vc.condition_id = c.condition_id
                                   GROUP BY vc.variant_id),
-- INDIVIDUAL CONDITION
    variant_to_individuals AS (SELECT v.variant_id, iv.individual_id
                               FROM variant v
                                        JOIN individual_variant iv
                                             ON iv.variant_id = v.variant_id),
    variant_indiv_condition AS (SELECT vti.variant_id,
                                       jsonb_agg(DISTINCT
                                                 jsonb_build_object(
                                                         'condition_id',
                                                         c.condition_id,
                                                         'condition',
                                                         c.condition
                                                 )) AS individual_conditions
                                FROM variant_to_individuals vti
                                         JOIN individual i
                                              ON vti.individual_id = i.individual_id
                                         JOIN individual_condition ic
                                              ON i.individual_id = ic.individual_id
                                         JOIN condition c
                                              ON ic.condition_id = c.condition_id
                                GROUP BY vti.variant_id),
    variant_indiv_treatment AS (SELECT vti.variant_id,
                                       jsonb_agg(jsonb_build_object(
                                               'treatment_id',
                                               t.treatment_id,
                                               'treatment',
                                               t.treatment_name
                                                 )) AS individual_treatments
                                FROM variant_to_individuals vti
                                         JOIN individual i
                                              ON vti.individual_id = i.individual_id
                                         JOIN treatment_record tr
                                              ON i.individual_id = tr.patient_id
                                         JOIN treatment t
                                              ON tr.treatment_id = t.treatment_id
                                GROUP BY vti.variant_id),
-- avg age of onset CPVT
    avg_age_onset_cpvt AS (SELECT v.variant_id,
                                  AVG(ic.age_of_onset) AS avg_age_of_onset_cpvt
                           FROM variant v
                                    JOIN individual_variant vi
                                         ON v.variant_id = vi.variant_id
                                    JOIN individual i
                                         ON vi.individual_id = i.individual_id
                                    JOIN individual_condition ic
                                         ON i.individual_id = ic.individual_id
                                    JOIN condition c
                                         ON ic.condition_id = c.condition_id
                           WHERE ic.age_of_onset IS NOT NULL
                             AND c.condition =
                                 'Catecholaminergic polymorphic ventricular tachycardia 1'
                           GROUP BY v.variant_id),
    sequence_variant_info AS (SELECT sv.sequence_variant_id,

                                     -- GENOMIC
                                     sa_g.ac           AS g_reference_sequence,
                                     et_g.edit_type_id AS g_edit_type_id,
                                     et_g.name         AS g_edit_type,
                                     sv.g_posedit_str,
                                     sv.g_pos_interval,
                                     sv.g_edit_ref,
                                     sv.g_edit_alt,
                                     sv.g_hgvs_string,

                                     -- CDNA
                                     sa_c.ac           AS c_reference_sequence,
                                     et_c.edit_type_id AS c_edit_type_id,
                                     et_c.name         AS c_edit_type,
                                     sv.c_posedit_str,
                                     sv.c_pos_interval,
                                     sv.c_start_offset,
                                     sv.c_end_offset,
                                     sv.c_edit_ref,
                                     sv.c_edit_alt,
                                     sv.c_hgvs_string,
                                     tx.hgnc           AS gene_symbol,

                                     -- PROTEIN
                                     sa_p.ac           AS p_reference_sequence,
                                     et_p.edit_type_id AS p_edit_type_id,
                                     et_p.name         AS p_edit_type,
                                     sv.p_posedit_str,
                                     pc.posedit_aa1    AS p_posedit_aa1,
                                     pc.posedit_aa3    AS p_posedit_aa3,
                                     sv.p_pos_interval,
                                     sv.p_start_aa,
                                     sv.p_end_aa,
                                     sv.p_edit_ref,
                                     sv.p_edit_alt,
                                     sv.p_hgvs_string

                              FROM sequence_variant sv
                                       LEFT JOIN protein_consequence pc
                                                 ON sv.sequence_variant_id =
                                                    pc.protein_consequence_id
                                       LEFT JOIN uta.seq_anno sa_g
                                                 ON sv.g_reference_sequence_id = sa_g.seq_anno_id
                                       LEFT JOIN uta.seq_anno sa_c
                                                 ON sv.c_reference_sequence_id = sa_c.seq_anno_id
                                       LEFT JOIN uta.transcript tx
                                                 ON sa_c.ac = tx.ac
                                       LEFT JOIN uta.seq_anno sa_p
                                                 ON sv.p_reference_sequence_id = sa_p.seq_anno_id
                                       LEFT JOIN edit_type et_g
                                                 ON sv.g_edit_type = et_g.edit_type_id
                                       LEFT JOIN edit_type et_c
                                                 ON sv.c_edit_type = et_c.edit_type_id
                                       LEFT JOIN edit_type et_p
                                                 ON sv.p_edit_type = et_p.edit_type_id)


SELECT v.variant_id,
       v.hgvs_string,
       vd.provenance,
       vci.variation_clinvar_id AS clinvar_variation_id,
       vni.num_individuals      AS num_individuals,
       avg_cpvt.avg_age_of_onset_cpvt,
       cs.clinical_significance_id,
       cs.clinical_significance,
       vc.conditions            AS clinvar_conditions,
       vic.individual_conditions,
       vit.individual_treatments,
       sv.*,
       ce.exons,
       sd.structure_domains
FROM variant v
         LEFT JOIN variant_clinvar_info vci
                   ON v.variant_id = vci.variant_id
         LEFT JOIN variant_dataset vd
                   ON v.variant_id = vd.variant_id
         LEFT JOIN variant_num_individuals_mv vni
                   ON v.variant_id = vni.variant_id
         LEFT JOIN clinical_significance cs
                   ON v.clinical_significance_id = cs.clinical_significance_id
         LEFT JOIN variant_conditions_clinvar vc
                   ON v.variant_id = vc.variant_id
         LEFT JOIN sequence_variant_info sv
                   ON v.sequence_variant_id = sv.sequence_variant_id
         LEFT JOIN variant_to_exon_v ce
                   ON sv.sequence_variant_id = ce.sequence_variant_id
         LEFT JOIN structure_domains sd
                   ON sv.sequence_variant_id = sd.sequence_variant_id
         LEFT JOIN variant_indiv_condition vic
                   ON v.variant_id = vic.variant_id
         LEFT JOIN variant_indiv_treatment vit
                   ON vic.variant_id = vit.variant_id
         LEFT JOIN avg_age_onset_cpvt avg_cpvt
                   ON v.variant_id = avg_cpvt.variant_id
ORDER BY v.variant_id
;

-- Indexes (basically every column is filterable so need an index on every single
-- except for the columns that display what an id maps to in words)

-- PK - variant_id
CREATE UNIQUE INDEX idx_variant_view_mv_variant_id ON variant_view_mv (variant_id);

-- datasets (for FILTER on JSONB)
CREATE INDEX variant_view_mv_provenance_idx ON variant_view_mv USING GIN (provenance);


-- num_individuals (for ORDER BY)
CREATE INDEX variant_view_mv_num_individuals_idx ON variant_view_mv (num_individuals);
-- avg_age_of_onset_cpvt (for ORDER BY)
CREATE INDEX variant_view_mv_avg_age_of_onset_cpvt_idx ON variant_view_mv (avg_age_of_onset_cpvt);
-- clinical_significance_id (for FILTER)
CREATE INDEX variant_view_mv_clinical_significance_id_idx ON variant_view_mv (clinical_significance_id);

-- clinvar_conditions (for FILTER on JSONB)
CREATE INDEX variant_view_mv_clinvar_conditions_idx ON variant_view_mv USING GIN (clinvar_conditions);

-- individual_conditions (for FILTER on JSONB)
CREATE INDEX variant_view_mv_individual_conditions_idx ON variant_view_mv USING GIN (individual_conditions);

-- individual_treatments (for FILTER on JSONB)
CREATE INDEX variant_view_mv_individual_treatments_idx ON variant_view_mv USING GIN (individual_treatments);

-- g_edit_type_id (for FILTER)
CREATE INDEX variant_view_mv_g_edit_type_id_idx ON variant_view_mv (g_edit_type_id);
-- g_pos_interval (for ORDER BY and FILTER on int4range)
CREATE INDEX variant_view_mv_g_pos_interval_idx ON variant_view_mv USING GIST (g_pos_interval);
-- g_hgvs_string (for LIKE filter)
CREATE INDEX variant_view_mv_g_hgvs_string_idx ON variant_view_mv (g_hgvs_string);
-- c_edit_type_id (for FILTER)
CREATE INDEX variant_view_mv_c_edit_type_id_idx ON variant_view_mv (c_edit_type_id);
-- c_pos_interval (for ORDER BY and FILTER on int4range)
CREATE INDEX variant_view_mv_c_pos_interval_idx ON variant_view_mv USING GIST (c_pos_interval);
-- c_hgvs_string (for LIKE filter)
CREATE INDEX variant_view_mv_c_hgvs_string_idx ON variant_view_mv (c_hgvs_string);
-- p_edit_type_id (for FILTER)
CREATE INDEX variant_view_mv_p_edit_type_id_idx ON variant_view_mv (p_edit_type_id);
-- p_pos_interval (for ORDER BY and FILTER on int4range)
CREATE INDEX variant_view_mv_p_pos_interval_idx ON variant_view_mv USING GIST (p_pos_interval);
-- p_posedit_aa1 (for LIKE filter)
CREATE INDEX variant_view_mv_p_posedit_aa1_idx ON variant_view_mv (p_posedit_aa1);
-- p_posedit_aa3 (for LIKE filter)
CREATE INDEX variant_view_mv_p_posedit_aa3_idx ON variant_view_mv (p_posedit_aa3);
-- p_hgvs_string (for LIKE filter)
CREATE INDEX variant_view_mv_p_hgvs_string_idx ON variant_view_mv (p_hgvs_string);

-- exons (for FILTER and ORDER BY on int4range)
CREATE INDEX variant_view_mv_exons_idx ON variant_view_mv USING GIST (exons);
-- structure_domains (for FILTER on JSONB)
CREATE INDEX variant_view_mv_structure_domains_idx ON variant_view_mv USING GIN (structure_domains);

