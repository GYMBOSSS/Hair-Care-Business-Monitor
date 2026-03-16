"""create all tables

Revision ID: xxxxx
Revises: 
Create Date: 2024-xx-xx
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'xxxxx'  # оставь как есть
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 1. Создаём businesses (независимая таблица)
    op.create_table('businesses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('address', sa.String(length=200), nullable=True),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 2. Создаём clients
    op.create_table('clients',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('comment', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('phone')
    )
    
    # 3. Создаём services
    op.create_table('services',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 4. Создаём users
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(length=80), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('password_hash', sa.String(length=200), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.UniqueConstraint('username')
    )
    
    # 5. Создаём appointments
    op.create_table('appointments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('service_id', sa.Integer(), nullable=False),
        sa.Column('appointment_time', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 6. Создаём invites
    op.create_table('invites',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('business_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # 7. Теперь добавляем внешние ключи (после создания всех таблиц)
    op.create_foreign_key('fk_clients_businesses', 'clients', 'businesses', ['business_id'], ['id'])
    op.create_foreign_key('fk_services_businesses', 'services', 'businesses', ['business_id'], ['id'])
    op.create_foreign_key('fk_users_businesses', 'users', 'businesses', ['business_id'], ['id'])
    op.create_foreign_key('fk_appointments_clients', 'appointments', 'clients', ['client_id'], ['id'])
    op.create_foreign_key('fk_appointments_services', 'appointments', 'services', ['service_id'], ['id'])
    op.create_foreign_key('fk_appointments_businesses', 'appointments', 'businesses', ['business_id'], ['id'])
    op.create_foreign_key('fk_invites_users', 'invites', 'users', ['user_id'], ['id'])
    op.create_foreign_key('fk_invites_businesses', 'invites', 'businesses', ['business_id'], ['id'])

def downgrade():
    # Удаляем внешние ключи
    op.drop_constraint('fk_invites_businesses', 'invites', type_='foreignkey')
    op.drop_constraint('fk_invites_users', 'invites', type_='foreignkey')
    op.drop_constraint('fk_appointments_businesses', 'appointments', type_='foreignkey')
    op.drop_constraint('fk_appointments_services', 'appointments', type_='foreignkey')
    op.drop_constraint('fk_appointments_clients', 'appointments', type_='foreignkey')
    op.drop_constraint('fk_users_businesses', 'users', type_='foreignkey')
    op.drop_constraint('fk_services_businesses', 'services', type_='foreignkey')
    op.drop_constraint('fk_clients_businesses', 'clients', type_='foreignkey')
    
    # Удаляем таблицы
    op.drop_table('invites')
    op.drop_table('appointments')
    op.drop_table('users')
    op.drop_table('services')
    op.drop_table('clients')
    op.drop_table('businesses')