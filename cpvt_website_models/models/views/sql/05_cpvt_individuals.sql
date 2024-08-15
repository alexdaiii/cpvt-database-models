DROP VIEW IF EXISTS cpvt_patients_v;


CREATE VIEW cpvt_patients_v AS
SELECT individual_id
FROM individual_condition ic
         JOIN condition c2
              ON ic.condition_id = c2.condition_id
WHERE c2.condition = 'Catecholaminergic polymorphic ventricular tachycardia 1'
  AND ic.has_condition = true;