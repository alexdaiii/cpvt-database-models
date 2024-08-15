# Define the trigger function in SQL
from sqlalchemy import DDL

check_accession = DDL(
    """
    CREATE OR REPLACE FUNCTION check_accession() RETURNS TRIGGER AS $$
    BEGIN
        IF NEW.parent_id IS NOT NULL AND 
            NEW.gene != (SELECT gene FROM structure WHERE structure_id = NEW.parent_id) THEN
            RAISE EXCEPTION 'Parent gene must be the same as child gene';
        END IF;
        RETURN NEW;
    END;
    $$ LANGUAGE plpgsql;
    """
)
check_accession_drop = DDL(
    """
    DROP FUNCTION IF EXISTS check_accession();
    """
)


check_accession_trigger = DDL(
    """
    CREATE TRIGGER check_accession_trigger
    BEFORE INSERT OR UPDATE ON structure
    FOR EACH ROW EXECUTE FUNCTION check_accession();
    """
)

check_accession_trigger_drop = DDL(
    """
    DROP TRIGGER IF EXISTS check_accession_trigger ON structure;
    """
)

# must be in order
variant_triggers = [
    check_accession,
    check_accession_trigger,
]

# must be in order
variant_triggers_drop = [
    check_accession_trigger_drop,
    check_accession_drop,
]


__all__ = [
    "variant_triggers",
    "variant_triggers_drop",
]
