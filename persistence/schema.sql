CREATE TABLE numbers (
    id SERIAL PRIMARY KEY,
    digit SMALLINT NOT NULL DEFAULT 0,
    pixels SMALLINT[][]
);

COMMENT ON TABLE numbers IS 'training data storing handwritten digits expressed as 8x8 pixels';
COMMENT ON COLUMN numbers.digit IS 'actual number representation from pixels (0-9)';
COMMENT ON COLUMN numbers.pixels IS 'representation of ink density within a 8x8-pixeled image';
