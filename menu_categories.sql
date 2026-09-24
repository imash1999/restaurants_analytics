CREATE TABLE menu_categories (
    id              BIGSERIAL PRIMARY KEY,
    restaurant_id   BIGINT NOT NULL
        REFERENCES restaurants(id)
        ON DELETE CASCADE,

    name            VARCHAR(150) NOT NULL,

    UNIQUE (restaurant_id, name)
);
