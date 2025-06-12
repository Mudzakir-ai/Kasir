from flask import Flask, render_template, request, redirect, url_for, session, send_file
import sqlite3
from datetime import datetime
import io
import pdfkit
import xlsxwriter

app = Flask(__name__)
app.secret_key = 'kasir_secret_key'
DATABASE = 'kasir.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        user = db.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, password)).fetchone()
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            return redirect(url_for('dashboard'))
        return render_template('login.html', error='Login gagal.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/produk')
def produk():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    items = db.execute('SELECT * FROM produk').fetchall()
    return render_template('produk.html', items=items)

@app.route('/produk/tambah', methods=['POST'])
def tambah_produk():
    nama = request.form['nama']
    harga = request.form['harga']
    stok = request.form['stok']
    db = get_db()
    db.execute('INSERT INTO produk (nama, harga, stok) VALUES (?, ?, ?)', (nama, harga, stok))
    db.commit()
    return redirect(url_for('produk'))

@app.route('/transaksi', methods=['GET', 'POST'])
def transaksi():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    produk = db.execute('SELECT * FROM produk').fetchall()
    if request.method == 'POST':
        items = request.form.getlist('produk_id')
        qtys = request.form.getlist('qty')
        total = 0
        detail = []
        for pid, qty in zip(items, qtys):
            if int(qty) > 0:
                prod = db.execute('SELECT * FROM produk WHERE id = ?', (pid,)).fetchone()
                subtotal = prod['harga'] * int(qty)
                total += subtotal
                detail.append((pid, int(qty), subtotal))
        bayar = float(request.form['bayar'])
        kembali = bayar - total
        cursor = db.cursor()
        cursor.execute('INSERT INTO transaksi (total, bayar, kembali) VALUES (?, ?, ?)', (total, bayar, kembali))
        tid = cursor.lastrowid
        for pid, qty, subtotal in detail:
            db.execute('INSERT INTO detail_transaksi (transaksi_id, produk_id, qty, subtotal) VALUES (?, ?, ?, ?)',
                       (tid, pid, qty, subtotal))
            db.execute('UPDATE produk SET stok = stok - ? WHERE id = ?', (qty, pid))
        db.commit()
        session['last_transaksi'] = {
            'detail': detail, 'total': total, 'bayar': bayar, 'kembali': kembali
        }
        return render_template('struk.html', detail=detail, total=total, bayar=bayar, kembali=kembali, produk=produk)
    return render_template('transaksi.html', produk=produk)

@app.route('/transaksi/pdf')
def cetak_pdf():
    data = session.get('last_transaksi')
    if not data:
        return redirect(url_for('transaksi'))
    db = get_db()
    produk = db.execute('SELECT * FROM produk').fetchall()
    rendered = render_template('struk_pdf.html', detail=data['detail'], total=data['total'],
                               bayar=data['bayar'], kembali=data['kembali'], produk=produk)
    pdf = pdfkit.from_string(rendered, False)
    return send_file(io.BytesIO(pdf), as_attachment=True, download_name='struk.pdf', mimetype='application/pdf')

@app.route('/laporan')
def laporan():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    db = get_db()
    data = db.execute('SELECT * FROM transaksi ORDER BY id DESC').fetchall()
    return render_template('laporan.html', data=data)

@app.route('/laporan/export')
def export_excel():
    db = get_db()
    data = db.execute('SELECT * FROM transaksi ORDER BY id DESC').fetchall()
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {'in_memory': True})
    sheet = workbook.add_worksheet('Laporan')
    headers = ['ID', 'Total', 'Bayar', 'Kembali', 'Tanggal']
    for col, h in enumerate(headers):
        sheet.write(0, col, h)
    for row_idx, t in enumerate(data, start=1):
        sheet.write(row_idx, 0, t['id'])
        sheet.write(row_idx, 1, t['total'])
        sheet.write(row_idx, 2, t['bayar'])
        sheet.write(row_idx, 3, t['kembali'])
        sheet.write(row_idx, 4, t['tanggal'])
    workbook.close()
    output.seek(0)
    return send_file(output, download_name='laporan_transaksi.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
