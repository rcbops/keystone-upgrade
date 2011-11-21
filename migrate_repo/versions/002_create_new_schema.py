from sqlalchemy import *
from migrate import *

from migrate.changeset import schema

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, object_mapper
from keystone.backends.sqlalchemy import models

from pprint import pprint

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    BASE = models.Base
    creation_tables = []
    for table in reversed(BASE.metadata.sorted_tables):
        creation_tables.append(table)
    meta.create_all(migrate_engine, tables=creation_tables, checkfirst=True)

    # Define models for all tables
    credentials = Table('credentials', meta, autoload=True)
    credentials_d5 = Table('credentials_d5', meta, autoload=True)
    endpoint_templates = Table('endpoint_templates', meta, autoload=True)
    endpoint_templates_d5 = Table('endpoint_templates_d5', meta, autoload=True)
    endpoints = Table('endpoints', meta, autoload=True)
    endpoints_d5 = Table('endpoints_d5', meta, autoload=True)
    roles = Table('roles', meta, autoload=True)
    roles_d5 = Table('roles_d5', meta, autoload=True)
    services = Table('services', meta, autoload=True)
    services_d5 = Table('services_d5', meta, autoload=True)
    tenants = Table('tenants', meta, autoload=True)
    tenants_d5 = Table('tenants_d5', meta, autoload=True)
    token = Table('token', meta, autoload=True)
    token_d5 = Table('token_d5', meta, autoload=True)
    user_roles = Table('user_roles', meta, autoload=True)
    user_roles_d5 = Table('user_roles_d5', meta, autoload=True)
    users = Table('users', meta, autoload=True)
    users_d5 = Table('users_d5', meta, autoload=True)

    # Copy over tenants
    result = tenants_d5.select().execute()
    for row in result:
        tenants.insert().values(
            name=row['id'], desc=row['desc'], enabled=row['enabled']).execute()
    result.close()

    # Copy over services
    result = services_d5.select().execute()
    for row in result:
        services.insert().values(name=row['id'], desc=row['desc']).execute()
    result.close()

    # Update *NEW* services.type field
    services.update().where(services.c.name=='compute').values(name='nova').execute()
    services.update().where(services.c.name=='nova').values(type='compute').execute()
    services.update().where(services.c.name=='image').values(name='glance').execute()
    services.update().where(services.c.name=='glance').values(type='image').execute()
    services.update().where(services.c.name=='identity').values(name='keystone').execute()
    services.update().where(services.c.name=='keystone').values(type='identity').execute()
    services.update().where(services.c.name=='storage').values(name='swift').execute()
    services.update().where(services.c.name=='swift').values(type='storage').execute()

    # Copy over users
    result = migrate_engine.execute(
        select(
            [(users_d5.c.id).label('name'), users_d5.c.password,
             users_d5.c.email, users_d5.c.enabled,
             (tenants.c.id).label('tenant_id')],
            users_d5.c.tenant_id==tenants.c.name
        )
    )
    for row in result:
        users.insert().values(
            name=row['name'], password=row['password'], email=row['email'],
            enabled=row['enabled'], tenant_id=row['tenant_id']).execute()
    result.close()

    # Copy over tokens
    result = migrate_engine.execute(
        select(
            [token_d5.c.id, (users.c.id).label('user_id'),
             (tenants.c.id).label('tenant_id'), token_d5.c.expires], 
            and_(token_d5.c.tenant_id==tenants.c.name,
                 token_d5.c.user_id==users.c.name)
        )
    )
    for row in result:
        token.insert().values(
            id=row['id'], user_id=row['user_id'], tenant_id=row['tenant_id'],
            expires=row['expires']).execute()
    result.close()

    # Copy over credentials
    result = migrate_engine.execute(
        select(
            [(users.c.id).label('user_id'), (tenants.c.id).label('tenant_id'),
             credentials_d5.c.type, credentials_d5.c.key,
             credentials_d5.c.secret],
            and_(credentials_d5.c.tenant_id==tenants.c.name,
                 credentials_d5.c.user_id==users.c.name)
        )
    )
    for row in result:
        credentials.insert().values(
            user_id=row['user_id'], tenant_id=row['tenant_id'],
            type=row['type'], key=row['key'], secret=row['secret']).execute()
    result.close()

    # Copy over endpoint_templates
    result = migrate_engine.execute(
        select(
            [endpoint_templates_d5.c.id, endpoint_templates_d5.c.region,
             (services.c.id).label('service_id'), 
             endpoint_templates_d5.c.public_url, endpoint_templates_d5.c.admin_url,
             endpoint_templates_d5.c.internal_url, endpoint_templates_d5.c.enabled,
             endpoint_templates_d5.c.is_global],
            and_(endpoint_templates_d5.c.service==services.c.name)
        )
    )
    for row in result:
        endpoint_templates.insert().values(id=row['id'], region=row['region'],
            service_id=row['service_id'], public_url=row['public_url'],
            admin_url=row['admin_url'], internal_url=row['internal_url'],
            enabled=row['enabled'], is_global=row['is_global']).execute()
    result.close()

    # Copy over endpoints
    result = migrate_engine.execute(
        select(
            [endpoints_d5.c.id, (tenants.c.id).label('tenant_id'),
             (endpoint_templates.c.id).label('endpoint_template_id')],
            and_(endpoints_d5.c.tenant_id==tenants.c.name,
                 endpoints_d5.c.endpoint_template_id==endpoint_templates.c.id)
        )
    )
    for row in result:
        endpoints.insert().values(id=row['id'], 
            tenant_id=row['tenant_id'],
            endpoint_template_id=row['endpoint_template_id']).execute()
    result.close()

    # Copy over roles - where service_id is NULL
    result = migrate_engine.execute(
        select(
            [(roles_d5.c.id).label('name'), roles_d5.c.desc,
             roles_d5.c.service_id],
            roles_d5.c.service_id==None
        )
    )
    for row in result:
        roles.insert().values(
            name=row['name'], desc=row['desc'],
            service_id=row['service_id']).execute()
    result.close()

    # Copy over roles - where service_id is NOT NULL
    result = migrate_engine.execute(
        select(
            [(roles_d5.c.id).label('name'), roles_d5.c.desc,
             (services.c.id).label('service_id')],
            roles_d5.c.service_id==services.c.name
        )
    )
    for row in result:
        roles.insert().values(
            name=row['name'], desc=row['desc'],
            service_id=row['service_id']).execute()
    result.close()

    # Copy over user_roles - where tenant_id is NULL
    result = migrate_engine.execute(
        select(
            [user_roles_d5.c.id, (users.c.id).label('user_id'),
             (roles.c.id).label('role_id'), user_roles_d5.c.tenant_id],
            and_(user_roles_d5.c.user_id==users.c.name,
                 user_roles_d5.c.role_id==roles.c.name,
                 user_roles_d5.c.tenant_id==None)
        )
    )
    for row in result:
        user_roles.insert().values(id=row['id'], 
            user_id=row['user_id'],
            role_id=row['role_id'],
            tenant_id=row['tenant_id']).execute()
    result.close()

    # Copy over user_roles - where tenant_id is NOT NULL
    result = migrate_engine.execute(
        select(
            [user_roles_d5.c.id, (users.c.id).label('user_id'),
             (roles.c.id).label('role_id'), (tenants.c.id).label('tenant_id')],
            and_(user_roles_d5.c.user_id==users.c.name,
                 user_roles_d5.c.role_id==roles.c.name,
                 user_roles_d5.c.tenant_id==tenants.c.name)
        )
    )
    for row in result:
        user_roles.insert().values(id=row['id'], 
            user_id=row['user_id'],
            role_id=row['role_id'],
            tenant_id=row['tenant_id']).execute()
    result.close()

    
def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    BASE = models.Base
    creation_tables = []
    for table in reversed(BASE.metadata.sorted_tables):
        creation_tables.append(table)
    meta.drop_all(migrate_engine, tables=creation_tables)
