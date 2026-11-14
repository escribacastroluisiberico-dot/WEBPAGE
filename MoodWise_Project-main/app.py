
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from pathlib import Path

app = Flask(__name__)
app.secret_key = "inventario-local"

DB_PATH = Path(__file__).with_name("inventario.db")


def conectar():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def inicializar_bd():
    with conectar() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS productos (
                id TEXT PRIMARY KEY,
                descripcion TEXT NOT NULL,
                stock INTEGER NOT NULL DEFAULT 0
            )
        """)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        producto_id = request.form["id"].strip()
        descripcion = request.form["descripcion"].strip()
        stock = int(request.form["stock"])

        try:
            with conectar() as db:
                db.execute(
                    "INSERT INTO productos VALUES (?, ?, ?)",
                    (producto_id, descripcion, stock)
                )
            flash("Producto registrado correctamente.", "success")
        except sqlite3.IntegrityError:
            flash("El ID ya existe.", "error")

        return redirect(url_for("index"))

    buscar = request.args.get("buscar", "").strip()

    with conectar() as db:
        productos = db.execute("""
            SELECT * FROM productos
            WHERE id LIKE ? OR descripcion LIKE ?
            ORDER BY id
        """, (f"%{buscar}%", f"%{buscar}%")).fetchall()

        total = db.execute(
            "SELECT COUNT(*) FROM productos"
        ).fetchone()[0]

        stock_total = db.execute(
            "SELECT COALESCE(SUM(stock), 0) FROM productos"
        ).fetchone()[0]

    return render_template(
        "index.html",
        productos=productos,
        buscar=buscar,
        total_productos=total,
        stock_total=stock_total
    )


@app.route("/editar/<producto_id>", methods=["GET", "POST"])
def editar(producto_id):
    with conectar() as db:
        producto = db.execute(
            "SELECT * FROM productos WHERE id = ?",
            (producto_id,)
        ).fetchone()

    if producto is None:
        flash("Producto no encontrado.", "error")
        return redirect(url_for("index"))

    if request.method == "POST":
        descripcion = request.form["descripcion"].strip()
        stock = int(request.form["stock"])

        with conectar() as db:
            db.execute("""
                UPDATE productos
                SET descripcion = ?, stock = ?
                WHERE id = ?
            """, (descripcion, stock, producto_id))

        flash("Producto actualizado.", "success")
        return redirect(url_for("index"))

    return render_template("editar.html", producto=producto)


@app.route("/eliminar/<producto_id>", methods=["POST"])
def eliminar(producto_id):
    with conectar() as db:
        db.execute(
            "DELETE FROM productos WHERE id = ?",
            (producto_id,)
        )

    flash("Producto eliminado.", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    inicializar_bd()
    app.run(debug=True)
