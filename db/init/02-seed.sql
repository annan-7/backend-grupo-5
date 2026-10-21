-- ============================================================
-- 02-seed.sql — Datos de demostración (primera inicialización)
--
-- UUIDs fijos y legibles para facilitar las pruebas manuales.
-- RUTs con dígito verificador válido (módulo 11).
-- Reservas coherentes con las reglas de negocio:
--   * dentro de las ventanas de disponibilidad del espacio,
--   * sin solapes, fechas en UTC.
-- ON CONFLICT DO NOTHING: re-ejecutar el script no duplica nada.
-- ============================================================

-- Espacios ---------------------------------------------------
INSERT INTO spaces (id, space_name, type, capacity, status, description, created_at, updated_at) VALUES
    ('a0000000-0000-4000-8000-000000000001', 'Sala Innovación',     'meeting_room',   10, 'active',      'Sala equipada con pizarra y proyector',        '2026-01-05 09:00:00+00', '2026-01-05 09:00:00+00'),
    ('a0000000-0000-4000-8000-000000000002', 'Oficina Cordillera',  'private_office',  6, 'active',      'Oficina privada con escritorio y lockers',     '2026-01-05 09:05:00+00', '2026-01-05 09:05:00+00'),
    ('a0000000-0000-4000-8000-000000000003', 'Open Space Araucanía','open_space',     20, 'active',      'Puestos de trabajo abiertos (hot desks)',      '2026-01-05 09:10:00+00', '2026-01-05 09:10:00+00'),
    ('a0000000-0000-4000-8000-000000000004', 'Sala Villarrica',     'meeting_room',    4, 'maintenance', 'En mantenimiento: cambio de proyector',        '2026-01-05 09:15:00+00', '2026-02-01 12:00:00+00')
ON CONFLICT (id) DO NOTHING;

-- Empresas (RUT con DV válido: 12345678-5, 22222222-2, 33333333-3)
INSERT INTO companies (id, company_name, rut, email, phone, address, created_at, updated_at) VALUES
    ('b0000000-0000-4000-8000-000000000001', 'Tecnología Andes SpA', '12345678-5', 'contacto@andes.cl',   '+56222334455', 'Av. Providencia 1234, Santiago',  '2026-01-06 10:00:00+00', '2026-01-06 10:00:00+00'),
    ('b0000000-0000-4000-8000-000000000002', 'Consultora Mapocho',   '22222222-2', 'hola@mapocho.cl',     '+56229876543', 'Calle Bandera 456, Santiago',     '2026-01-06 10:05:00+00', '2026-01-06 10:05:00+00'),
    ('b0000000-0000-4000-8000-000000000003', 'Startup Nahuel',       '33333333-3', 'equipo@nahuel.dev',   '+56225556677', 'Av. Las Condes 7890, Santiago',   '2026-01-06 10:10:00+00', '2026-01-06 10:10:00+00')
ON CONFLICT (id) DO NOTHING;

-- Disponibilidades --------------------------------------------
-- Sala Innovación: lunes a viernes 09:00-18:00
INSERT INTO availabilities (id, space_id, weekday, opening_time, closing_time, created_at, updated_at) VALUES
    ('c0000000-0000-4000-8000-000000000001', 'a0000000-0000-4000-8000-000000000001', 'monday',    '09:00:00', '18:00:00', '2026-01-07 08:00:00+00', '2026-01-07 08:00:00+00'),
    ('c0000000-0000-4000-8000-000000000002', 'a0000000-0000-4000-8000-000000000001', 'tuesday',   '09:00:00', '18:00:00', '2026-01-07 08:00:00+00', '2026-01-07 08:00:00+00'),
    ('c0000000-0000-4000-8000-000000000003', 'a0000000-0000-4000-8000-000000000001', 'wednesday', '09:00:00', '18:00:00', '2026-01-07 08:00:00+00', '2026-01-07 08:00:00+00'),
    ('c0000000-0000-4000-8000-000000000004', 'a0000000-0000-4000-8000-000000000001', 'thursday',  '09:00:00', '18:00:00', '2026-01-07 08:00:00+00', '2026-01-07 08:00:00+00'),
    ('c0000000-0000-4000-8000-000000000005', 'a0000000-0000-4000-8000-000000000001', 'friday',    '09:00:00', '18:00:00', '2026-01-07 08:00:00+00', '2026-01-07 08:00:00+00'),
-- Oficina Cordillera: lunes y viernes 09:00-18:00
    ('c0000000-0000-4000-8000-000000000006', 'a0000000-0000-4000-8000-000000000002', 'monday',    '09:00:00', '18:00:00', '2026-01-07 08:05:00+00', '2026-01-07 08:05:00+00'),
    ('c0000000-0000-4000-8000-000000000007', 'a0000000-0000-4000-8000-000000000002', 'friday',    '09:00:00', '18:00:00', '2026-01-07 08:05:00+00', '2026-01-07 08:05:00+00')
ON CONFLICT (id) DO NOTHING;

-- Reservas ------------------------------------------------------
-- 2030-01-10 es jueves (ventana 09-18 de Sala Innovación) ✓
-- 2030-01-14 es lunes (ventana 09-18 de Oficina Cordillera) ✓
-- La completada es histórica (2026-09-01, martes, dentro de la ventana) ✓
INSERT INTO reservations (id, space_id, company_id, start_date, end_date, status, reason, created_at, updated_at) VALUES
    ('d0000000-0000-4000-8000-000000000001', 'a0000000-0000-4000-8000-000000000001', 'b0000000-0000-4000-8000-000000000001', '2030-01-10 10:00:00+00', '2030-01-10 12:00:00+00', 'confirmed', 'Planificación trimestral',        '2026-01-08 11:00:00+00', '2026-01-09 09:00:00+00'),
    ('d0000000-0000-4000-8000-000000000002', 'a0000000-0000-4000-8000-000000000002', 'b0000000-0000-4000-8000-000000000002', '2030-01-14 09:00:00+00', '2030-01-14 11:00:00+00', 'pending',   'Reunión de directorio',           '2026-01-08 11:30:00+00', '2026-01-08 11:30:00+00'),
    ('d0000000-0000-4000-8000-000000000003', 'a0000000-0000-4000-8000-000000000001', 'b0000000-0000-4000-8000-000000000003', '2026-09-01 15:00:00+00', '2026-09-01 16:30:00+00', 'completed', 'Taller de onboarding (histórico)', '2026-08-20 10:00:00+00', '2026-09-01 16:35:00+00')
ON CONFLICT (id) DO NOTHING;
