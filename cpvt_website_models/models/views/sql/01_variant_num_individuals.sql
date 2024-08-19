DROP VIEW IF EXISTS variant_num_individuals_v CASCADE;
CREATE VIEW variant_num_individuals_v AS
SELECT variant.variant_id,
       COUNT(DISTINCT individual_id) AS num_individuals
FROM variant
         LEFT JOIN individual_variant
                   ON variant.variant_id = individual_variant.variant_id
GROUP BY variant.variant_id;
-- CREATE UNIQUE INDEX variant_num_individuals_variant_id_idx ON variant_num_individuals_mv (variant_id);
-- CREATE INDEX variant_num_individuals_num_individuals_idx ON variant_num_individuals_mv (num_individuals);
