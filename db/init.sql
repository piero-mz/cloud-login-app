-- Script de inicialización de la base de datos
-- Crea la tabla de usuarios y dos usuarios de prueba (datos ficticios).
-- Las contraseñas están guardadas con hash bcrypt (costo 12), nunca en texto plano.
--   admin   -> Admin123!
--   mlopez  -> Maria2026!
-- Es idempotente: se puede ejecutar varias veces sin duplicar datos.

CREATE TABLE IF NOT EXISTS usuarios (
    id             SERIAL PRIMARY KEY,
    usuario        VARCHAR(50)  NOT NULL UNIQUE,
    password_hash  VARCHAR(255) NOT NULL,
    nombre         VARCHAR(100) NOT NULL,
    creado_en      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO usuarios (usuario, password_hash, nombre) VALUES
    ('admin',  '$2b$12$qgVZm6WU36D6s5ZaLPsF3.wI/hWHDJE/Uc80MMUjDGT4TCJdRlgzm', 'Administrador del Sistema'),
    ('mlopez', '$2b$12$JWwtO3IsMpkrryfSL8sFEuLRYsy7tBO9Lout28NmnDZEK0lVYk0VK', 'María López')
ON CONFLICT (usuario) DO NOTHING;
