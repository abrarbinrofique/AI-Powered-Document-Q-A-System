-- Insert sample project for the default tenant
-- Run this after the database is initialized

-- Get the default tenant ID
DO $$
DECLARE
    default_tenant_id UUID;
BEGIN
    SELECT tenant_id INTO default_tenant_id FROM tenants WHERE name = 'default-tenant';

    -- Insert a sample project
    INSERT INTO projects (tenant_id, name, description, status)
    VALUES (
        default_tenant_id,
        'Sample DDQ Project',
        'Sample project for testing the DDQ Agent system',
        'active'
    );

    RAISE NOTICE 'Sample project created successfully';
END $$;
