from django.db import migrations

SQL_UP = """
ALTER TABLE public.crm_entidade DROP COLUMN IF EXISTS cnpj;
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint
    WHERE conrelid = 'public.crm_entidade'::regclass
      AND conname = 'crm_entidade_documento_key'
  ) THEN
    ALTER TABLE public.crm_entidade ADD CONSTRAINT crm_entidade_documento_key UNIQUE (documento);
  END IF;
END$$;
"""

SQL_DOWN = """
ALTER TABLE public.crm_entidade ADD COLUMN IF NOT EXISTS cnpj varchar(18);
ALTER TABLE public.crm_entidade DROP CONSTRAINT IF EXISTS crm_entidade_documento_key;
"""

class Migration(migrations.Migration):
    dependencies = [
        # a sua última migração do app crm, por ex. ("crm", "0001_initial")
        ("crm", "0001_initial"),
    ]
    operations = [
        migrations.RunSQL(SQL_UP, SQL_DOWN),
    ]
