import pymysql
pymysql.install_as_MySQLdb()
import MySQLdb
setattr(MySQLdb, 'version_info', (2, 2, 1, 'final', 0))
