CREATE TABLE IF NOT EXISTS farmers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    village TEXT NOT NULL,
    phone TEXT NOT NULL,
    land_acres REAL NOT NULL CHECK (land_acres > 0),
    crop_preference TEXT NOT NULL,
    registered_on TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS seeds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    crop_type TEXT NOT NULL,
    variety TEXT NOT NULL,
    season TEXT NOT NULL,
    price_per_kg REAL NOT NULL CHECK (price_per_kg >= 0),
    stock_kg REAL NOT NULL CHECK (stock_kg >= 0),
    reorder_level_kg REAL NOT NULL CHECK (reorder_level_kg >= 0)
);

CREATE TABLE IF NOT EXISTS distributions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    farmer_id INTEGER NOT NULL,
    seed_id INTEGER NOT NULL,
    quantity_kg REAL NOT NULL CHECK (quantity_kg > 0),
    subsidy_percent REAL NOT NULL CHECK (subsidy_percent >= 0 AND subsidy_percent <= 100),
    total_cost REAL NOT NULL CHECK (total_cost >= 0),
    distributed_on TEXT NOT NULL,
    notes TEXT,
    FOREIGN KEY (farmer_id) REFERENCES farmers(id),
    FOREIGN KEY (seed_id) REFERENCES seeds(id)
);
