'backup.py' is a simple script used to backup Obiba products on a server.

The backup is done as follows:
* keeps X months per year
* keeps last Y days per month
* each product backs up:
  * specified files (with/out) wildcards in the backup config 
  * specified folders in the backup config
  * specified databases in the backup config
  * specified mongo DBs in the backup config
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
	    files: [/folder/*.csv,/folder/toto.sh]
	    folders: [/var/www/mica.org]
	    mongodbs:
	      host: localhost
	      port: 27017
	    databases:
	      names: [mica]
	      usr: dbadmin
	      pwd: '123456'
	  opal:
	    folders: [/var/lib/opal/,/var/log/opal/]
	    databases:
	      names: [opal_key,opal_data]
	      usr: dbadmin
	      pwd: '123456'

To send content of the backup destination folder to a remote server add the following in the config file:

### Example of a rsync file:

	keep:
	  days: 5
	  month: 3
	destination: /obiba/backups
	...
	rsync:
	  destination: user@backup-server.blabla.ca:/data/local-server
	  pem: /some/where/backup-user.pem
	  


To send a collection of folders outside of the backup destination folder add the following in the config file:

	keep:
	  days: 5
	  month: 3
	...
	rsyncs:
	  - folder:
	    path: /var/my/folder
	    excludes: [/toto,/tata]
	  - folder:
	    path: /etc/my/folder
	  - ...
	rsync:
	  destination: user@backup-server.blabla.ca:/data/local-server
	  pem: /some/where/backup-user.pem

The backups on the remote server user the project or folder names without any timestamp information. This is too enforce backing up of only the latest local backup on the remote server.

### To backup a collection of MySQL DBs use a _like_ pattern instead of names:

	keep:
	  days: 5
	  month: 3
	destination: /obiba/backups
	projects:
	  mica:
	    keep:
	      days: 5
	      month: 6
	    files: [/folder/*.csv,/folder/toto.sh]
	    folders: [/var/www/mica.org]
	    databases:
	      prefix: 'live%'
	      usr: dbadmin
	      pwd: '123456'

### Required files:

The only files requires are:

* obiba/src/main/python/backup.py (make sure this file is executable (chmod +x))
* obiba/src/main/python/backup.conf


### Automating the backup:

On Linux you can create a crontab as follows:

00 00 * * 1-5 /path/to/backup.py > /path/to/backup.log 2>&1

The above backups from Monday-Friday at 00h00 (mid-night)

### TODOs

* use regex for mongoDB names so as to prevent listing each DB name
* replace prefix and use regex for MySQL DB names
* make _keep_ and _destination_ optional
