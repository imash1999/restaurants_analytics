CREATE TABLE order_items (
    id              BIGSERIAL PRIMARY KEY,

    order_id        BIGINT NOT NULL
        REFERENCES orders(id)
        ON DELETE CASCADE,

    dish_id         BIGINT NOT NULL
        REFERENCES dishes(id),

    quantity        INTEGER NOT NULL CHECK (quantity > 0),

    unit_price      NUMERIC(10,2) NOT NULL,

    subtotal        NUMERIC(10,2) NOT NULL
);
