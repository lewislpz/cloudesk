BEGIN;

SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

CREATE TABLE foundation_metadata (
    singleton boolean PRIMARY KEY DEFAULT true,
    component text NOT NULL,
    schema_generation bigint NOT NULL,
    installed_at timestamptz NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT foundation_metadata_singleton_check CHECK (singleton),
    CONSTRAINT foundation_metadata_component_check CHECK (component = 'clouddesk'),
    CONSTRAINT foundation_metadata_schema_generation_check CHECK (schema_generation > 0)
);

COMMENT ON TABLE foundation_metadata IS
    'Technical schema marker for migration and generated-query verification; not a product domain table.';

INSERT INTO foundation_metadata (singleton, component, schema_generation)
VALUES (true, 'clouddesk', 1);

COMMIT;
