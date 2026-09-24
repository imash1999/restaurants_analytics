CREATE TABLE restaurant_hours (
    id              BIGSERIAL PRIMARY KEY,

    restaurant_id   BIGINT NOT NULL
        REFERENCES restaurants(id)
        ON DELETE CASCADE,

    day_of_week     SMALLINT NOT NULL,

    open_time       TIME,
    close_time      TIME,

    UNIQUE (restaurant_id, day_of_week)
);
