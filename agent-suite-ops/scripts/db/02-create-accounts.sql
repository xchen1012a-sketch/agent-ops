-- ===========================================================================
-- enterprise-agent-suite :: MySQL accounts and privilege matrix
-- ===========================================================================
-- Implements the permission matrix in
-- agent-suite-ops/docs/runbooks/deployment-design.md §5 and ADR-0011.
--
-- Run as MySQL root/admin. Passwords are placeholders (__CHANGE_ME__) and
-- MUST be replaced at provision time via Docker secret or env injection.
--
-- Accounts:
--   legal_agent            legal_agent_db           SELECT/INSERT/UPDATE/DELETE
--   legal_migration        legal_agent_db           above + DDL
--   recruitment_agent      recruitment_agent_db     SELECT/INSERT/UPDATE/DELETE
--   recruitment_migration  recruitment_agent_db     above + DDL
--   data_query_agent       data_query_agent_db      SELECT/INSERT/UPDATE/DELETE
--   data_query_migration   data_query_agent_db      above + DDL
--   data_query_reader      shop_db                  SELECT only
--
-- System DBs (mysql, information_schema, performance_schema, sys) are revoked
-- explicitly; default DENY for everything not granted here.
-- ===========================================================================

-- ---------------------------------------------------------------------------
-- legal_agent : runtime read/write
-- ---------------------------------------------------------------------------
CREATE USER IF NOT EXISTS 'legal_agent'@'%'
    IDENTIFIED BY '__CHANGE_ME_LEGAL_AGENT__';
ALTER USER 'legal_agent'@'%' IDENTIFIED BY '__CHANGE_ME_LEGAL_AGENT__';
GRANT SELECT, INSERT, UPDATE, DELETE ON legal_agent_db.* TO 'legal_agent'@'%';

-- legal_migration : Alembic migrations (DDL)
CREATE USER IF NOT EXISTS 'legal_migration'@'%'
    IDENTIFIED BY '__CHANGE_ME_LEGAL_MIGRATION__';
ALTER USER 'legal_migration'@'%' IDENTIFIED BY '__CHANGE_ME_LEGAL_MIGRATION__';
GRANT ALL PRIVILEGES ON legal_agent_db.* TO 'legal_migration'@'%';

-- ---------------------------------------------------------------------------
-- recruitment_agent : runtime read/write
-- ---------------------------------------------------------------------------
CREATE USER IF NOT EXISTS 'recruitment_agent'@'%'
    IDENTIFIED BY '__CHANGE_ME_RECRUITMENT_AGENT__';
ALTER USER 'recruitment_agent'@'%' IDENTIFIED BY '__CHANGE_ME_RECRUITMENT_AGENT__';
GRANT SELECT, INSERT, UPDATE, DELETE ON recruitment_agent_db.* TO 'recruitment_agent'@'%';

-- recruitment_migration : Alembic migrations (DDL)
CREATE USER IF NOT EXISTS 'recruitment_migration'@'%'
    IDENTIFIED BY '__CHANGE_ME_RECRUITMENT_MIGRATION__';
ALTER USER 'recruitment_migration'@'%' IDENTIFIED BY '__CHANGE_ME_RECRUITMENT_MIGRATION__';
GRANT ALL PRIVILEGES ON recruitment_agent_db.* TO 'recruitment_migration'@'%';

-- ---------------------------------------------------------------------------
-- data_query_agent : runtime read/write on its own DB only
-- ---------------------------------------------------------------------------
CREATE USER IF NOT EXISTS 'data_query_agent'@'%'
    IDENTIFIED BY '__CHANGE_ME_DATA_QUERY_AGENT__';
ALTER USER 'data_query_agent'@'%' IDENTIFIED BY '__CHANGE_ME_DATA_QUERY_AGENT__';
GRANT SELECT, INSERT, UPDATE, DELETE ON data_query_agent_db.* TO 'data_query_agent'@'%';

-- data_query_migration : Alembic migrations (DDL)
CREATE USER IF NOT EXISTS 'data_query_migration'@'%'
    IDENTIFIED BY '__CHANGE_ME_DATA_QUERY_MIGRATION__';
ALTER USER 'data_query_migration'@'%' IDENTIFIED BY '__CHANGE_ME_DATA_QUERY_MIGRATION__';
GRANT ALL PRIVILEGES ON data_query_agent_db.* TO 'data_query_migration'@'%';

-- ---------------------------------------------------------------------------
-- data_query_reader : read-only on shop_db (NL2SQL execution)
-- ---------------------------------------------------------------------------
CREATE USER IF NOT EXISTS 'data_query_reader'@'%'
    IDENTIFIED BY '__CHANGE_ME_DATA_QUERY_READER__';
ALTER USER 'data_query_reader'@'%' IDENTIFIED BY '__CHANGE_ME_DATA_QUERY_READER__';
GRANT SELECT ON shop_db.* TO 'data_query_reader'@'%';

-- ---------------------------------------------------------------------------
-- Defense in depth: explicitly REVOKE system DBs from all app accounts.
-- ---------------------------------------------------------------------------
REVOKE ALL PRIVILEGES ON mysql.* FROM 'legal_agent'@'%';
REVOKE ALL PRIVILEGES ON mysql.* FROM 'legal_migration'@'%';
REVOKE ALL PRIVILEGES ON mysql.* FROM 'recruitment_agent'@'%';
REVOKE ALL PRIVILEGES ON mysql.* FROM 'recruitment_migration'@'%';
REVOKE ALL PRIVILEGES ON mysql.* FROM 'data_query_agent'@'%';
REVOKE ALL PRIVILEGES ON mysql.* FROM 'data_query_migration'@'%';
REVOKE ALL PRIVILEGES ON mysql.* FROM 'data_query_reader'@'%';

FLUSH PRIVILEGES;
