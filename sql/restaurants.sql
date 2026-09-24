CREATE TABLE restaurants (
    id              BIGSERIAL PRIMARY KEY,
    source_id       VARCHAR(100) UNIQUE,
    name            VARCHAR(255) NOT NULL,
    description     TEXT,

    category        VARCHAR(100),
    price_range     VARCHAR(10),

    rating          NUMERIC(2,1),
    rating_count    INTEGER DEFAULT 0,

    address         TEXT,
    zip_code        VARCHAR(20),

    latitude        NUMERIC(9,6),
    longitude       NUMERIC(9,6),

    is_active       BOOLEAN DEFAULT TRUE,

    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
