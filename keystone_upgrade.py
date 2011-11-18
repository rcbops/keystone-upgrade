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

from sqlalchemy import *
from ConfigParser import ConfigParser
from migrate.versioning.api import version_control, version, upgrade
from migrate.versioning.exceptions import DatabaseAlreadyControlledError
from pprint import pprint

conf_file = "/etc/keystone/keystone.conf"
section_name = "keystone.backends.sqlalchemy"
initial_version = 0
migrate_repository = 'migrate_repo'

config = ConfigParser()
config.read(conf_file)

engine = config.get(section_name, "sql_connection")
latest_version = version(migrate_repository)
try:
    version_control(engine, migrate_repository, version=initial_version)
except DatabaseAlreadyControlledError:
    pass
