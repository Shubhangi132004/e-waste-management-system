"""Initial EcoSmart schema.

Revision ID: 0001_initial_schema
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("full_name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_table(
        "reports",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("issue_type", sa.String(length=80), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("image_filename", sa.String(length=255), nullable=True),
        sa.Column("latitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("longitude", sa.Numeric(10, 7), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="Pending"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_reports_user_id", "reports", ["user_id"])
    op.create_index("ix_reports_issue_type", "reports", ["issue_type"])
    op.create_index("ix_reports_status", "reports", ["status"])
    op.create_table(
        "collection_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("report_id", sa.Integer(), sa.ForeignKey("reports.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(length=80), nullable=False),
        sa.Column("collection_address", sa.String(length=500), nullable=False),
        sa.Column("preferred_date", sa.Date(), nullable=False),
        sa.Column("collection_status", sa.String(length=20), nullable=False, server_default="Requested"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_collection_requests_user_id", "collection_requests", ["user_id"])
    op.create_index("ix_collection_requests_report_id", "collection_requests", ["report_id"])
    op.create_index("ix_collection_requests_collection_status", "collection_requests", ["collection_status"])


def downgrade():
    op.drop_table("collection_requests")
    op.drop_table("reports")
    op.drop_index("ix_users_role", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
