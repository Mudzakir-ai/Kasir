CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT
);

CREATE TABLE IF NOT EXISTS produk (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nama TEXT,
    harga REAL,
    stok INTEGER
);

CREATE TABLE IF NOT EXISTS transaksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    total REAL,
    bayar REAL,
    kembali REAL,
    tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS detail_transaksi (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaksi_id INTEGER,
    produk_id INTEGER,
    qty INTEGER,
    subtotal REAL,
    FOREIGN KEY(transaksi_id) REFERENCES transaksi(id),
    FOREIGN KEY(produk_id) REFERENCES produk(id)
);

INSERT INTO users (username, password) VALUES ('admin', 'admin');
