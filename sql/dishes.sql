CREATE TABLE dishes (
    id              BIGSERIAL PRIMARY KEY,

    restaurant_id   BIGINT NOT NULL
        REFERENCES restaurants(id)
        ON DELETE CASCADE,

    category_id     BIGINT
        REFERENCES menu_categories(id),

    name            VARCHAR(255) NOT NULL,
    description     TEXT,

    price           NUMERIC(10,2) NOT NULL,

    image_url       TEXT,

    is_available    BOOLEAN DEFAULT TRUE,

    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
