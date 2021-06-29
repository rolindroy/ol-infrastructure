# noqa: WPS226
"""Creation and revocation statements used for Vault role definitions."""

# These strings are passed through the `.format` method so the variables that need to remain in the template
# to be passed to Vault are wrapped in 4 pairs of braces. TMM 2020-09-01

import json
from enum import Enum

postgres_role_statements = {
    "approle": {
        "create": "CREATE ROLE {app_name};",
        "revoke": "DROP ROLE {app_name};",
    },
    "admin": {
        "create": """CREATE USER "{{{{name}}}}" WITH PASSWORD '{{{{password}}}}' VALID UNTIL '{{{{expiration}}}}'
          IN ROLE "rds_superuser" INHERIT CREATEROLE CREATEDB;
          GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{{{{name}}}}" WITH GRANT OPTION;
          GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{{{{name}}}}" WITH GRANT OPTION;""",
        "revoke": """GRANT "{{{{name}}}}" TO {app_name} WITH ADMIN OPTION;
          REASSIGN OWNED BY "{{{{name}}}}" TO "{app_name}";
          DROP OWNED BY "{{{{name}}}}";
          REVOKE "{app_name}" FROM "{{{{name}}}}";
          REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM "{{{{name}}}}";
          REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM "{{{{name}}}}";
          REVOKE USAGE ON SCHEMA public FROM "{{{{name}}}}";
          DROP USER "{{{{name}}}}";""",
    },
    "app": {
        "create": """CREATE USER "{{{{name}}}}" WITH PASSWORD '{{{{password}}}}' VALID UNTIL '{{{{expiration}}}}'
          IN ROLE "{app_name}" INHERIT;
          GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{{{{name}}}}" WITH GRANT OPTION;
          GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{{{{name}}}}" WITH GRANT OPTION;
          GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "{app_name}" WITH GRANT OPTION;
          GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "{app_name}" WITH GRANT OPTION;
          SET ROLE "{{{{name}}}}";
          ALTER DEFAULT PRIVILEGES FOR USER "{{{{name}}}}" IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES
          TO "{{{{name}}}}" WITH GRANT OPTION;
          ALTER DEFAULT PRIVILEGES FOR USER "{{{{name}}}}" IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES
          TO "{{{{name}}}}" WITH GRANT OPTION;
          SET ROLE "{app_name}";
          ALTER DEFAULT PRIVILEGES FOR ROLE "{app_name}" IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES
          TO "{app_name}" WITH GRANT OPTION;
          ALTER DEFAULT PRIVILEGES FOR ROLE "{app_name}" IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES
          TO "{app_name}" WITH GRANT OPTION;
          RESET ROLE;
          ALTER ROLE "{{{{name}}}}" SET ROLE "{app_name}";""",
        "revoke": """GRANT "{{{{name}}}}" TO {app_name} WITH ADMIN OPTION;
          REASSIGN OWNED BY "{{{{name}}}}" TO "{app_name}";
          DROP OWNED BY "{{{{name}}}}";
          REVOKE "{app_name}" FROM "{{{{name}}}}";
          REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM "{{{{name}}}}";
          REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM "{{{{name}}}}";
          REVOKE USAGE ON SCHEMA public FROM "{{{{name}}}}";
          DROP USER "{{{{name}}}}";""",
    },
    "readonly": {
        "create": """CREATE USER "{{{{name}}}}" WITH PASSWORD '{{{{password}}}}' VALID UNTIL '{{{{expiration}}}}';
          GRANT SELECT ON ALL TABLES IN SCHEMA public TO "{{{{name}}}}";
          GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO "{{{{name}}}}";
          SET ROLE "{{{{name}}}}";
          ALTER DEFAULT PRIVILEGES FOR USER "{{{{name}}}}" IN SCHEMA public GRANT SELECT ON TABLES TO "{{{{name}}}}"
          WITH GRANT OPTION;
          ALTER DEFAULT PRIVILEGES FOR USER "{{{{name}}}}" IN SCHEMA public GRANT SELECT ON SEQUENCES TO "{{{{name}}}}"
          WITH GRANT OPTION;
          RESET ROLE;""",
        "revoke": """GRANT "{{{{name}}}}" TO {app_name} WITH ADMIN OPTION;
          REASSIGN OWNED BY "{{{{name}}}}" TO "{app_name}";
          DROP OWNED BY "{{{{name}}}}";
          REVOKE "{app_name}" FROM "{{{{name}}}}";
          REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM "{{{{name}}}}";
          REVOKE ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public FROM "{{{{name}}}}";
          REVOKE USAGE ON SCHEMA public FROM "{{{{name}}}}";
          DROP USER "{{{{name}}}}";""",
    },
}

mysql_role_statements = {
    "admin": {
        "create": "CREATE USER '{{{{name}}}}'@'%' IDENTIFIED BY '{{{{password}}}}';"
        "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, REFERENCES, INDEX, ALTER, "
        "CREATE TEMPORARY TABLES, LOCK TABLES, EXECUTE, CREATE VIEW, SHOW VIEW, "
        "CREATE ROUTINE, ALTER ROUTINE, EVENT, TRIGGER ON `%`.* TO '{{{{name}}}}' "
        "WITH GRANT OPTION; GRANT RELOAD, LOCK TABLES ON *.* to '{{{{name}}}}';",
        "revoke": "DROP USER '{{{{name}}}}';",
    },
    "app": {
        "create": "CREATE USER '{{{{name}}}}'@'%' IDENTIFIED BY '{{{{password}}}}';"
        "GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, INDEX, DROP, ALTER, REFERENCES"  # noqa: Q000
        "CREATE TEMPORARY TABLES, LOCK TABLES ON {app_name}.* TO '{{{{name}}}}'@'%';",
        "revoke": "DROP USER '{{{{name}}}}';",
    },
    "readonly": {
        "create": "CREATE USER '{{{{name}}}}'@'%' IDENTIFIED BY '{{{{password}}}}';"
        "GRANT SELECT, SHOW VIEW ON `%`.* TO '{{{{name}}}}'@'%';",
        "revoke": "DROP USER '{{{{name}}}}';",
    },
}

mongodb_role_statements = {
    "admin": {
        "create": json.dumps(
            {"roles": [{"role": "superuser"}, {"role": "root"}], "db": "admin"}
        ),
        "revoke": json.dumps({"db": "admin"}),
    },
    "app": {
        "create": json.dumps({"roles": [{"role": "readWrite"}], "db": "{app_name}"}),
        "revoke": json.dumps({"db": "{app_name}"}),
    },
    "readonly": {"create": json.dumps({"roles": [{"role": "read"}]}), "revoke": ""},
}


class VaultPKIKeyTypeBits(int, Enum):
    rsa = 4096
    ec = 256
