# Database initialization scripts

Run order is enforced by filename prefix. Apply with a MySQL 8 client as an
administrative account (root or `GRANT OPTION` holder):

```bash
mysql -h mysql -u root -p < 01-create-schemas.sql
mysql -h mysql -u root -p < 02-create-accounts.sql
```

Replace `__CHANGE_ME_*__` placeholders in `02-create-accounts.sql` with strong
secrets before applying. The Docker entrypoint binds these scripts at
`/docker-entrypoint-initdb.d/` so a fresh `mysql_data` volume auto-applies them
on first container start.

Sources:
- `agent-suite-ops/docs/runbooks/deployment-design.md` §5 (permission matrix)
- `agent-suite-ops/docs/adr/0011-deployment-and-database-permissions.md`
