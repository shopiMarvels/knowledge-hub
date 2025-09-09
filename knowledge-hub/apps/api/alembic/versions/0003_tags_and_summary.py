from alembic import op
import sqlalchemy as sa

revision = '0003_tags_and_summary'
down_revision = '0002_documents_chunks'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('documents', sa.Column('summary', sa.Text(), nullable=True))
    op.create_table(
        'document_tags',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('document_id', sa.Integer(), sa.ForeignKey('documents.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()')),
    )
    op.create_index('ix_document_tags_document_id', 'document_tags', ['document_id'])
    op.create_index('ix_document_tags_tag', 'document_tags', ['tag'])

def downgrade():
    op.drop_index('ix_document_tags_tag', table_name='document_tags')
    op.drop_index('ix_document_tags_document_id', table_name='document_tags')
    op.drop_table('document_tags')
    op.drop_column('documents', 'summary')
