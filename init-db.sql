-- init-db.sql — PostgreSQL initialization (runs on first container start)
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create pgvector HNSW index support (if needed later)
-- This runs inside the coolbreeze database automatically
SELECT 'PostgreSQL initialized with pgvector for CoolBreeze AC' AS status;
