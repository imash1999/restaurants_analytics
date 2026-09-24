CREATE TABLE orders (
    id              BIGSERIAL PRIMARY KEY,

    user_id         BIGINT NOT NULL
        REFERENCES users(id),

    restaurant_id   BIGINT NOT NULL
        REFERENCES restaurants(id),

    status          VARCHAR(30) NOT NULL,

    subtotal        NUMERIC(10,2) NOT NULL,
    delivery_fee    NUMERIC(10,2) DEFAULT 0,
    discount        NUMERIC(10,2) DEFAULT 0,

    total_amount    NUMERIC(10,2) NOT NULL,

    delivery_address TEXT,

    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
