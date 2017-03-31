#!/usr/bin/env python

####################################################################################################################
# 'backup.py' is a simple script used to backup Obiba products on a server.
#
# The backup is done as follows:
#   - keeps two months per year
#   - each month keeps the last five backup days
#   - each product backs up:
#       - specified folders in the backup config
#       - specified databases in the backup config
####################################################################################################################

import os
from datetime import datetime
from datetime import date
import subprocess
import gzip
from subprocess import call
import shutil
import traceback
import yaml
import glob


class ObibaBackup:
    CONFIG_FILE = os.path.join(os.path.dirname(__file__), "backup.conf")

    def run(self):
        """
        This is where everything starts
        """
        try:
            print "# Obiba backup started (%s)" % datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.__loadConfig()
            self.__setup()
            self.__backupRemoteProjects()
            self.__backupProjects()
        except Exception, e:
            print '*' * 80
            print "* ERROR"
            print
            print traceback.format_exc()
            print '*' * 80
        finally:
            print "# Obiba backup completed (%s)" % datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    ####################################################################################################################
    # P R I V A T E     M E T H O D S
    ####################################################################################################################

    def __loadConfig(self):
        configFile = open(self.CONFIG_FILE, 'r')
        self.config = yaml.load(configFile)
        configFile.close()

    ####################################################################################################################
    def __setup(self):
        """
        Setup basically creates the daily backup folder for each project
        """

        backupFolder = self.config['destination']
        self.__createBackupFolder(backupFolder)

        # create the project based backup folder
        today = date.today()

        if 'projects' in self.config:
            for project in self.config['projects'].iterkeys():
                timestamp = datetime.now().strftime('%d-%H-%M-%S')
                backupDestination = os.path.join(backupFolder, project, str(today.year), today.strftime('%m'), timestamp)
                self.__createBackupFolder(backupDestination)
                self.config['projects'][project]['destination'] = backupDestination

    ####################################################################################################################
    def __backupRemoteProjects(self):
        if 'rsyncs' in self.config:
            for rsync in self.config['rsyncs']:
                if 'folder' in rsync:
                    self.__backupToRemoteServer(rsync['folder'])

    ####################################################################################################################
    def __backupProjects(self):
        if 'projects' in self.config:
            for project in self.config['projects'].iterkeys():
                print "Backing up %s..." % project
                self.__backupProject(self.config['projects'][project], project)

    ####################################################################################################################
    def __backupProject(self, project, projectName):
        destination = project['destination']
        self.__cleanup(os.path.dirname(destination), projectName)
        if 'files' in project:
            self.__backupFiles(project['files'], destination)
        if 'folders' in project:
            self.__backupFolders(project['folders'], destination)
        if 'mongodbs' in project:
            self.__backupMongodbs(project['mongodbs'], destination)
        if 'databases' in project:
            self.__backupDatabases(project['databases'], destination)

        self.__backupToRemoteServer(destination, projectName)

    ####################################################################################################################
    def __backupToRemoteServer(self, source):
        if 'rsync' in self.config and 'destination' in self.config['rsync']:
            excludes = []
            if 'excludes' in source:
                for exclude in source['excludes']:
                    excludes.append('--exclude')
                    excludes.append('%s' % exclude)

            folder = os.path.basename(source['path'])
            source = os.path.join(source['path'], '')
            destination = "%s/%s" % (self.config['rsync']['destination'], folder)
            publicKey = ''

            if 'pem' in self.config['rsync']:
                publicKey = "ssh -i %s" % self.config['rsync']['pem']

            print "Backing up %s to remote server %s..." % (source, self.config['rsync']['destination'])
            print "rsync -Atrave '%s' %s %s %s" % (publicKey, ' '.join(str(x) for x in excludes), source, destination)
            result = subprocess.check_output(
              [
                  'rsync',
                  '-Atrave',
                  publicKey,
                  source,
                  destination
              ] + excludes
            )

            print result

    ####################################################################################################################
    def __cleanup(self, destination, project):
        month = self.config['keep']['month']
        days = self.config['keep']['days']
        if 'keep' in self.config['projects'][project]:
            if 'month' in self.config['projects'][project]['keep']:
                month = self.config['projects'][project]['keep']['month']
            if 'days' in self.config['projects'][project]['keep']:
                days = self.config['projects'][project]['keep']['days']
        self.__cleanupFolders(os.path.dirname(destination), month)
        self.__cleanupFolders(destination, days)

    ####################################################################################################################
    def __cleanupFolders(self, destination, keep):
        sortedFolders = self.__getSortedFolderList(destination)
        self.__deleteFolders(len(sortedFolders) - keep, destination, sortedFolders)

    ####################################################################################################################
    def __backupFiles(self, files, destination):
        for file in files:
            print "\tBacking up file %s to %s" % (file, destination)
            for fileItem in glob.glob(file):
                if os.path.isfile(fileItem):
                  destinationPath = os.path.join(destination, os.path.dirname(fileItem)[1:])
                  if not os.path.exists(destinationPath):
                    os.makedirs(destinationPath)
                  shutil.copy(fileItem, destinationPath)

    ####################################################################################################################
    def __backupFolders(self, folders, destination):
        for folder in folders:
            print "\tBacking up folder %s to %s" % (folder, destination)
            filename = "%s.tar.gz" % (os.path.basename(folder))
            destinationPath = os.path.join(destination, folder[1:])
            if not os.path.exists(destinationPath):
              os.makedirs(destinationPath)
            backupFile = os.path.join(destinationPath, filename)
            result = call(["tar", "czfP", backupFile, folder])
            if result != 0:
                print "Failed to tar %s" % backupFile

    ####################################################################################################################
    def __backupMongodbs(self, mongodbs, destination):
        for mongodb in mongodbs['names']:
            self.__backupMongodb(mongodb, destination, mongodbs['host'], mongodbs['port'])

    ####################################################################################################################
    def __backupMongodb(self, mongodb, destination, host, port):
        print "\tBacking up mongodb %s to %s" % (mongodb, destination)
        subprocess.check_output(
            [
                'mongodump',
                '--host', '%s' % host,
                '-d', '%s' % mongodb,
                '--port', '%s' % port,
                '-o', '%s' % destination,
                '--gzip'
            ])

    ####################################################################################################################
    def __backupDatabases(self, databases, destination):
        if 'prefix' in databases:
            names = self.__listDatabases(databases['prefix'], databases['usr'], databases['pwd'])
        else:
            names = databases['names']

        for database in names:
            self.__backupDatabase(database, destination, databases['usr'], databases['pwd'])

    ####################################################################################################################
    def __listDatabases(self, prefix, usr, pwd):
        matchingCommand = "SHOW DATABASES LIKE '" + prefix + "'"
        listCommand = ["mysql", "-u", usr, "-p" + pwd, "-B", "-N", "-e", matchingCommand]
        listProcess = subprocess.Popen(listCommand, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        listOutput = listProcess.communicate()[0]
        return listOutput.rstrip().split('\n')

    ####################################################################################################################
    def __backupDatabase(self, database, destination, usr, pwd):
        print "\tBacking up database %s to %s" % (database, destination)
        filename = "%s.sql.gz" % (os.path.basename(database))
        backupFile = os.path.join(destination, filename)

        dumpCommand = ["mysqldump", "-u", usr, "-p" + pwd, database]
        dumpProcess = subprocess.Popen(dumpCommand, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        dumpOutput = dumpProcess.communicate()[0]

        zipFile = gzip.open(backupFile, "wb")
        zipFile.write(dumpOutput)
        zipFile.close()

    ####################################################################################################################
    def __deleteFolders(self, deleteCount, destination, sortedFolders):
        if deleteCount > 0:
            foldersToDelete = sortedFolders[:deleteCount]
            for folder in foldersToDelete:
                print "\tDeleting %s" % os.path.join(destination, folder[0])
                shutil.rmtree(os.path.join(destination, folder[0]))

    ####################################################################################################################
    def __getSortedFolderList(self, destination):
        files = os.listdir(destination)
        file_date_tuple_list = [(x, os.path.getmtime(os.path.join(destination, x))) for x in files]
        file_date_tuple_list.sort(key=lambda x: x[1])
        return file_date_tuple_list

    ####################################################################################################################
    def __createBackupFolder(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

####################################################################################################################
# S C R I P T    M A I N    E N T R Y
####################################################################################################################

if __name__ == "__main__":
    ObibaBackup().run()

