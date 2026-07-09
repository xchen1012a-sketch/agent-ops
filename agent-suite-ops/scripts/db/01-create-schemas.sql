-- ===========================================================================
-- enterprise-agent-suite :: MySQL schema initialization
-- ===========================================================================
-- Creates the 4 schemas defined in ADR-0011.
-- Idempotent: safe to re-run. Schema names are project constants and come
-- from the deployment design runbook (agent-suite-ops/docs/runbooks/deployment-design.md).
-- Account grants live in 02-create-accounts.sql.
-- ===========================================================================

CREATE DATABASE IF NOT EXISTS legal_agent_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS recruitment_agent_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS data_query_agent_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

CREATE DATABASE IF NOT EXISTS shop_db
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;
