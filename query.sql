ALTER TABLE refunds
ADD orderitem_id VARCHAR(15);


UPDATE refunds 
SET orderitem_id = 5
WHERE amount = 1.99;


CREATE TABLE refunds_new (
    id INTEGER PRIMARY KEY,
    payment_id INTEGER,
    amount REAL,
    reason TEXT,
    created_at DATETIME,
    status TEXT
);

INSERT INTO refunds_new (id, payment_id, amount, reason, created_at, status)
SELECT id, payment_id, amount, reason, created_at, status
FROM refunds;
DROP TABLE refunds;
ALTER TABLE refunds_new RENAME TO refunds;



update reviews
set user_id = 2
where user_id = 1

UPDATE products
SET seller_id = 2
WHERE id BETWEEN 16 AND 30;



DROP table sellers
DROP table checkouts