DROP FUNCTION IF EXISTS build_ui_filter CASCADE;

--- NEW STATEMENT

CREATE OR REPLACE FUNCTION build_ui_filter(data_values jsonb, component text,
                                           queryParam text, label text,
                                           ordinal integer,
                                           histogram jsonb DEFAULT NULL,
                                           hidden boolean DEFAULT FALSE,
                                           shortLabel text DEFAULT NULL,
                                           description text DEFAULT NULL
)
    RETURNS jsonb AS
$$
BEGIN
    RETURN jsonb_build_object('values', data_values,
                              'component', component,
                              'queryParam', queryParam,
                              'label', label,
                              'ordinal', ordinal,
                              'histogram', histogram,
                              'hidden', hidden,
                              'shortLabel', shortLabel,
                              'description', description
           );
END;
$$ LANGUAGE plpgsql;
