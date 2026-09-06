-- name: GetFoundationMetadata :one
SELECT component, schema_generation
FROM foundation_metadata
WHERE singleton = true;
