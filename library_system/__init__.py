import pymysql

# Django 6 validates MySQLdb version and rejects PyMySQL's default compatibility
# marker (1.4.6). Override to a supported mysqlclient-compatible version.
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"
pymysql.install_as_MySQLdb()

# XAMPP often ships MariaDB 10.4; Django 6 requires 10.6+ by default.
# Allow local development on XAMPP by bypassing this strict version gate.
try:
	from django.db.backends.mysql.base import DatabaseWrapper
	from django.db.backends.mysql.features import DatabaseFeatures

	DatabaseWrapper.check_database_version_supported = lambda self: None
	DatabaseFeatures.can_return_columns_from_insert = False
	DatabaseFeatures.can_return_rows_from_bulk_insert = False
except Exception:
	# Safe to ignore if Django hasn't initialized this backend yet.
	pass
