#!/usr/bin/env python
# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack LLC.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from ConfigParser import ConfigParser
from sqlalchemy import *
import sys
from migrate.versioning.api import version_control, drop_version_control, version, upgrade
# See LP bug #719834. sqlalchemy-migrate changed location of
# exceptions.py after 0.6.0.
try:
    from migrate.versioning.exceptions import DatabaseAlreadyControlledError, DatabaseNotControlledError
except ImportError:
    from migrate.exceptions import DatabaseAlreadyControlledError, DatabaseNotControlledError

conf_file = "/etc/keystone/keystone.conf"
section_name = "keystone.backends.sqlalchemy"
initial_version = 0
migrate_repository = 'migrate_repo'

config = ConfigParser()
config.read(conf_file)

engine = config.get(section_name, "sql_connection")
latest_version = version(migrate_repository)

# Add Version control to the DB
print ".. Placing the keystone db under version control"
try:
    version_control(engine, migrate_repository, version=initial_version)
except DatabaseAlreadyControlledError:
    pass

# Upgrade the db to version latest_version
print ".. Upgrading the keystone db to the latest version"
try:
    upgrade(engine, migrate_repository, version=latest_version)
except:
    e = sys.exc_info()[1]
    print "Caught an unkown exception: %s" % e

# Drop Version control from the DB
print ".. Removing the keystone db from version control"
try:
    drop_version_control(engine, migrate_repository)
except DatabaseNotControlledError:
    pass

print ".. Execute ./keystone_commands.bash to verify the db looks good"
