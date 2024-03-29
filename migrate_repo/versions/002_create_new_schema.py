from sqlalchemy import *
from migrate import *

from migrate.changeset import schema

from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, object_mapper

Base = declarative_base()

# Define associations first
class UserRoleAssociation(Base):
    __tablename__ = 'user_roles'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    role_id = Column(Integer, ForeignKey('roles.id'))
    tenant_id = Column(Integer, ForeignKey('tenants.id'))
    __table_args__ = (UniqueConstraint("user_id", "role_id", "tenant_id"), {})

    user = relationship('User')


class Endpoints(Base):
    __tablename__ = 'endpoints'
    id = Column(Integer, primary_key=True)
    tenant_id = Column(Integer)
    endpoint_template_id = Column(Integer, ForeignKey('endpoint_templates.id'))
    __table_args__ = (
        UniqueConstraint("endpoint_template_id", "tenant_id"), {})


# Define objects
class Role(Base):
    __tablename__ = 'roles'
    __api__ = 'role'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    desc = Column(String(255))
    service_id = Column(Integer, ForeignKey('services.id'))
    __table_args__ = (
        UniqueConstraint("name", "service_id"), {})

class Service(Base):
    __tablename__ = 'services'
    __api__ = 'service'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True)
    type = Column(String(255))
    desc = Column(String(255))

class Tenant(Base):
    __tablename__ = 'tenants'
    __api__ = 'tenant'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True)
    desc = Column(String(255))
    enabled = Column(Integer)


class User(Base):
    __tablename__ = 'users'
    __api__ = 'user'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True)
    password = Column(String(255))
    email = Column(String(255))
    enabled = Column(Integer)
    tenant_id = Column(Integer, ForeignKey('tenants.id'))
    roles = relationship(UserRoleAssociation, cascade="all")
    credentials = relationship('Credentials', backref='user', cascade="all")

class Credentials(Base):
    __tablename__ = 'credentials'
    __api__ = 'credentials'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    tenant_id = Column(Integer, ForeignKey('tenants.id'), nullable=True)
    type = Column(String(20))  # ('Password','APIKey','EC2')
    key = Column(String(255))
    secret = Column(String(255))


class Token(Base):
    __tablename__ = 'token'
    __api__ = 'token'
    id = Column(String(255), primary_key=True, unique=True)
    user_id = Column(Integer)
    tenant_id = Column(Integer)
    expires = Column(DateTime)

class EndpointTemplates(Base):
    __tablename__ = 'endpoint_templates'
    __api__ = 'endpoint_template'
    id = Column(Integer, primary_key=True)
    region = Column(String(255))
    service_id = Column(Integer, ForeignKey('services.id'))
    public_url = Column(String(2000))
    admin_url = Column(String(2000))
    internal_url = Column(String(2000))
    enabled = Column(Boolean)
    is_global = Column(Boolean)

def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine)
    creation_tables = []
    for table in reversed(Base.metadata.sorted_tables):
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
    creation_tables = []
    for table in reversed(Base.metadata.sorted_tables):
        creation_tables.append(table)
    meta.drop_all(migrate_engine, tables=creation_tables)
