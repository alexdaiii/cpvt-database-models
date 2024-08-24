DROP MATERIALIZED VIEW IF EXISTS protein_consequence_mv CASCADE;
CREATE MATERIALIZED VIEW protein_consequence_mv AS
WITH p_info AS (SELECT DISTINCT ON (p_hgvs_string) p_hgvs_string,
                                                   p_pos_interval,
                                                   posedit_aa1,
                                                   posedit_aa3,
                                                   et.edit_type_id,
                                                   et.name AS edit_type,
                                                   sa.ac   AS refseq
                FROM sequence_variant sv
                         JOIN edit_type et
                              ON sv.p_edit_type = et.edit_type_id
                         JOIN protein_consequence pc
                              ON sv.sequence_variant_id =
                                 pc.protein_consequence_id
                         JOIN uta.seq_anno sa
                              ON sv.p_reference_sequence_id = sa.seq_anno_id
                WHERE p_hgvs_string IS NOT NULL),
     p_mapped_from AS (SELECT p_hgvs_string,
                              (SELECT jsonb_agg(
                                              DISTINCT jsonb_build_object(
                                              'sequence_variant_id',
                                              sv.sequence_variant_id,
                                              'g_hgvs_string',
                                              sv.g_hgvs_string,
                                              'c_hgvs_string', sv.c_hgvs_string
                                                       ))) AS sequence_variants
                       FROM sequence_variant sv
                       WHERE p_hgvs_string IS NOT NULL
                       GROUP BY p_hgvs_string),
     p_clinvar_conditions AS (SELECT sub.p_hgvs_string,
                                     jsonb_agg(DISTINCT c) AS clinvar_conditions
                              FROM (SELECT sv.p_hgvs_string,
                                           jsonb_array_elements(vvm.clinvar_conditions) AS c
                                    FROM sequence_variant sv
                                             JOIN variant_view_mv vvm
                                                  ON sv.sequence_variant_id =
                                                     vvm.sequence_variant_id
                                    WHERE sv.p_hgvs_string IS NOT NULL) AS sub
                              GROUP BY sub.p_hgvs_string),
     p_individual_conditions AS (SELECT sub.p_hgvs_string,
                                        jsonb_agg(DISTINCT c) AS individual_conditions
                                 FROM (SELECT sv.p_hgvs_string,
                                              jsonb_array_elements(vvm.individual_conditions) AS c
                                       FROM sequence_variant sv
                                                JOIN variant_view_mv vvm
                                                     ON sv.sequence_variant_id =
                                                        vvm.sequence_variant_id
                                       WHERE sv.p_hgvs_string IS NOT NULL) AS sub
                                 GROUP BY sub.p_hgvs_string),
     p_individual_treatments AS (SELECT sub.p_hgvs_string,
                                        jsonb_agg(DISTINCT c) AS individual_treatments
                                 FROM (SELECT sv.p_hgvs_string,
                                              jsonb_array_elements(vvm.individual_treatments) AS c
                                       FROM sequence_variant sv
                                                JOIN variant_view_mv vvm
                                                     ON sv.sequence_variant_id =
                                                        vvm.sequence_variant_id
                                       WHERE sv.p_hgvs_string IS NOT NULL) AS sub
                                 GROUP BY sub.p_hgvs_string),
     p_variant_info AS (SELECT sv.p_hgvs_string,
                               (SELECT jsonb_agg(
                                               DISTINCT jsonb_build_object(
                                               'variant_id', v.variant_id,
                                               'clinical_significance_id',
                                               vvm.clinical_significance_id,
                                               'clinical_significance',
                                               vvm.clinical_significance,
                                               'variant_hgvs_string',
                                               v.hgvs_string
                                                        )
                                       )) AS variant_info
                        FROM sequence_variant sv
                                 JOIN variant v
                                      ON sv.sequence_variant_id = v.sequence_variant_id
                                 JOIN variant_view_mv vvm
                                      ON v.variant_id = vvm.variant_id
                        WHERE sv.p_hgvs_string IS NOT NULL
                        GROUP BY sv.p_hgvs_string),
     p_tot_individuals AS (SELECT sv.p_hgvs_string,
                                  SUM(
                                          vvm.num_individuals
                                  ) AS num_individuals
                           FROM sequence_variant sv
                                    JOIN variant v
                                         ON sv.sequence_variant_id = v.sequence_variant_id
                                    JOIN variant_view_mv vvm
                                         ON v.variant_id = vvm.variant_id
                           WHERE sv.p_hgvs_string IS NOT NULL
                           GROUP BY sv.p_hgvs_string),
     p_structure_domains AS (SELECT sv.p_hgvs_string,
                                    jsonb_agg(DISTINCT jsonb_build_object(
                                            'structure_id', pvs.structure_id,
                                            'structure_domain', pvs.name,
                                            'structure_domain_symbol',
                                            pvs.symbol
                                                       )) AS structure_domains
                             FROM sequence_variant sv
                                      JOIN p_variant_to_structure_v pvs
                                           ON sv.sequence_variant_id =
                                              pvs.sequence_variant_id
                             GROUP BY sv.p_hgvs_string),
     p_exons AS (SELECT sv.p_hgvs_string,
                        MIN(lower(ce.exons)) AS exon_start,
                        -- NOTE: THIS IS NON INCLUSIVE [start, end)
                        MAX(upper(ce.exons)) AS exon_end
                 FROM sequence_variant sv
                          LEFT JOIN variant_to_exon_v ce
                                    ON sv.sequence_variant_id =
                                       ce.sequence_variant_id
                 WHERE sv.p_hgvs_string IS NOT NULL
                 GROUP BY sv.p_hgvs_string),
     p_prov AS (SELECT sub.p_hgvs_string,
                       jsonb_agg(DISTINCT c) AS provenance
                FROM (SELECT sv.p_hgvs_string,
                             jsonb_array_elements(vvm.provenance) AS c
                      FROM sequence_variant sv
                               JOIN variant_view_mv vvm
                                    ON sv.sequence_variant_id =
                                       vvm.sequence_variant_id
                      WHERE sv.p_hgvs_string IS NOT NULL) AS sub
                GROUP BY sub.p_hgvs_string),
     p_all AS (SELECT DISTINCT ON (sv.p_hgvs_string) sv.p_hgvs_string,
                                                     p_info.p_pos_interval,
                                                     p_info.posedit_aa1,
                                                     p_info.posedit_aa3,
                                                     p_info.edit_type_id,
                                                     p_info.edit_type,
                                                     p_info.refseq,
                                                     p_mapped_from.sequence_variants,
                                                     p_variant_info.variant_info,
                                                     p_structure_domains.structure_domains,
                                                     p_exons.exon_start,
                                                     p_exons.exon_end,
                                                     p_tot_individuals.num_individuals,
                                                     p_clinvar_conditions.clinvar_conditions,
                                                     p_individual_conditions.individual_conditions,
                                                     p_individual_treatments.individual_treatments,
                                                     p_prov.provenance
               FROM sequence_variant sv
                        LEFT JOIN p_info
                                  ON sv.p_hgvs_string = p_info.p_hgvs_string
                        LEFT JOIN p_mapped_from
                                  ON sv.p_hgvs_string = p_mapped_from.p_hgvs_string
                        LEFT JOIN p_clinvar_conditions ON sv.p_hgvs_string =
                                                          p_clinvar_conditions.p_hgvs_string
                        LEFT JOIN p_individual_conditions ON sv.p_hgvs_string =
                                                             p_individual_conditions.p_hgvs_string
                        LEFT JOIN p_individual_treatments ON sv.p_hgvs_string =
                                                             p_individual_treatments.p_hgvs_string
                        LEFT JOIN p_variant_info ON sv.p_hgvs_string =
                                                    p_variant_info.p_hgvs_string
                        LEFT JOIN p_tot_individuals ON sv.p_hgvs_string =
                                                       p_tot_individuals.p_hgvs_string
                        LEFT JOIN p_structure_domains ON sv.p_hgvs_string =
                                                         p_structure_domains.p_hgvs_string
                        LEFT JOIN p_exons
                                  ON sv.p_hgvs_string = p_exons.p_hgvs_string
                        LEFT JOIN p_prov
                                  ON sv.p_hgvs_string = p_prov.p_hgvs_string
               WHERE sv.p_hgvs_string IS NOT NULL)
SELECT *
FROM p_all
ORDER BY p_all.p_pos_interval;


-- create index
CREATE UNIQUE INDEX protein_consequence_mv_p_hgvs_string_idx
    ON protein_consequence_mv (p_hgvs_string);
-- int4range index
CREATE INDEX protein_consequence_mv_p_pos_interval_idx
    ON protein_consequence_mv USING GIST (p_pos_interval);
-- text indexes
CREATE INDEX protein_consequence_mv_posedit_aa1_idx
    ON protein_consequence_mv USING BTREE (posedit_aa1);
CREATE INDEX protein_consequence_mv_posedit_aa3_idx
    ON protein_consequence_mv USING BTREE (posedit_aa3);

/**
  Regular Btree indexes (plain numbers)
p_exons.exon_start,
p_exons.exon_end,
p_tot_individuals.num_individuals,
 */
CREATE INDEX protein_consequence_mv_exon_start_idx
    ON protein_consequence_mv USING BTREE (exon_start);
CREATE INDEX protein_consequence_mv_exon_end_idx
    ON protein_consequence_mv USING BTREE (exon_end);
CREATE INDEX protein_consequence_mv_num_individuals_idx
    ON protein_consequence_mv USING BTREE (num_individuals);


/**
  GIN indexes (jsonb) - everything else
 */
CREATE INDEX protein_consequence_mv_sequence_variants_idx
    ON protein_consequence_mv USING GIN (sequence_variants);
CREATE INDEX protein_consequence_mv_variant_info_idx
    ON protein_consequence_mv USING GIN (variant_info);
CREATE INDEX protein_consequence_mv_structure_domains_idx
    ON protein_consequence_mv USING GIN (structure_domains);
CREATE INDEX protein_consequence_mv_clinvar_conditions_idx
    ON protein_consequence_mv USING GIN (clinvar_conditions);
CREATE INDEX protein_consequence_mv_individual_conditions_idx
    ON protein_consequence_mv USING GIN (individual_conditions);
CREATE INDEX protein_consequence_mv_individual_treatments_idx
    ON protein_consequence_mv USING GIN (individual_treatments);
CREATE INDEX protein_consequence_mv_provenance_idx
    ON protein_consequence_mv USING GIN (provenance);



