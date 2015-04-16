# import pymysql
# pymysql.install_as_MySQLdb()
#import gdb
import pymysql
pymysql.install_as_MySQLdb()
import django.conf
django.conf.settings.configure(DEBUG=True, TEMPLATE_DEBUG=True)
