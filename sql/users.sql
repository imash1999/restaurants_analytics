CREATE TABLE users (
    id              BIGSERIAL PRIMARY KEY,

    username        VARCHAR(100) UNIQUE NOT NULL,
    email           VARCHAR(255) UNIQUE NOT NULL,

    password_hash   TEXT NOT NULL,

    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
