INSERT INTO restaurants (
    source_id,
    name,
    category,
    price_range,
    address,
    zip_code,
    latitude,
    longitude,
    rating,
    rating_count
)
SELECT
    NULLIF(TRIM(source_id), ''),
    NULLIF(TRIM(name), ''),
    NULLIF(TRIM(category), ''),
    NULLIF(TRIM(price_range), ''),
    NULLIF(TRIM(full_address), ''),
    NULLIF(TRIM(zip_code), ''),
    NULLIF(TRIM(lat), '')::numeric(9,6),
    NULLIF(TRIM(lng), '')::numeric(9,6),
    NULLIF(TRIM(score), '')::numeric(2,1),
    COALESCE(NULLIF(TRIM(ratings), '')::integer, 0)
FROM stg_restaurants;
