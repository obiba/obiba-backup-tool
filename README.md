'backup.py' is a simple script used to backup Obiba products on a server.

The backup is done as follows:
* keeps X months per year
* each month keeps the last Y backup days
* each product backs up:
  * specified folders in the backup config
  * specified databases in the backup config
  * the backup days and months can be customized per project

### Example of a config file:

	keep:
	  days: 5
	  month: 3
	destination: /obiba/backups
	projects:
	  mica:
	    keep:
	      days: 5
	      month: 6
	    folders: [/var/www/mica.org]
	    databases:
	      names: [mica]
	      usr: root
	      pwd: 123456
	  opal:
	    folders: [/var/lib/opal/,/var/log/opal/]
	    databases:
	      names: [opal_key,opal_data]
	      usr: root
	      pwd: 123456


### Required files:

The only files requires are:

* obiba/src/main/python/backup.py (make sure this file is executable (chmod +x))
* obiba/src/main/python/backup.conf


### Automating the backup:

On Linux you can create a crontab as follows:

00 00 * * 1-5 /path/to/backup.py > /path/to/backup.log 2>&1

The above backups from Monday-Friday at 00h00 (mid-night)
