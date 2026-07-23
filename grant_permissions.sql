-- Grant SERVICE ROLE permissions
-- Created: Thursday Jul 23, 2026, 4:32 PM (UTC-6)
-- Last edited: Thursday Jul 23, 2026, 4:41 PM (UTC-6)

GRANT SELECT, INSERT, UPDATE, DELETE ON public.clients TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.client_contexts TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.client_reference_files TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.published_articles TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.runs TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.unresolved_items TO service_role;

-- Also grant on core tables
GRANT SELECT, INSERT, UPDATE, DELETE ON public.authority_models TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.css_templates TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.provider_settings TO service_role;

-- Verify permissions were granted
SELECT grantee, table_schema, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'service_role'
ORDER BY table_name;
