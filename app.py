"""
Mimito Dev — Full Flask App with Database + Admin Panel
"""
import os
import uuid
import smtplib
import json
from datetime import datetime, timezone as tz
from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from models import db, Inquiry, InquiryItem, Product, init_db, seed_products

app = Flask(__name__)

# Database config
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL or 'sqlite:///mimito.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'mimito-dev-secret-2026')

# Email config
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME', '')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD', '')

# Init database
db.init_app(app)

# ─── Gunicorn hooks (run before first request on Railway) ──────────────────
import os

def post_fork(server, worker):
    """Run migrations once per worker process (with file-based mutex so only one does it)."""
    lock_file = '/tmp/mimito_migrations.lock'
    if os.path.exists(lock_file):
        return
    try:
        with app.app_context():
            _do_migrations()
        open(lock_file, 'w').close()
    except Exception as e:
        print(f"  [migrate] worker error: {e}")

def worker_int(server):
    pass

def _do_migrations():
    """Add missing columns to existing PostgreSQL tables."""
    from sqlalchemy import text
    try:
        conn = db.engine.connect()
        existing = [r[0] for r in conn.execute(text(
            "SELECT column_name FROM information_schema.columns WHERE table_name='inquiries'"
        )).fetchall()]
        for col_name, sql in [
            ("public_id", "ALTER TABLE inquiries ADD COLUMN public_id VARCHAR(12)"),
            ("status",    "ALTER TABLE inquiries ADD COLUMN status VARCHAR(50) DEFAULT 'New'"),
            ("notes",     "ALTER TABLE inquiries ADD COLUMN notes TEXT"),
            ("lang",      "ALTER TABLE inquiries ADD COLUMN lang VARCHAR(5) DEFAULT 'en'"),
            ("updated_at","ALTER TABLE inquiries ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
            ("phone",     "ALTER TABLE inquiries ADD COLUMN phone VARCHAR(50)"),
        ]:
            if col_name not in existing:
                try:
                    conn.execute(text(sql))
                    conn.commit()
                    print(f"  [migrate] added: {col_name}")
                except Exception as e:
                    print(f"  [migrate] {col_name}: {e}")
        conn.close()
    except Exception as e:
        print(f"  [migrate] connection error: {e}")

# ─── Translations (simplified — just the ones we need for the admin)
TRANSLATIONS = {
    'en': {},
    'mk': {}
}

PRODUCTS_HARDCODED = {
    'shirts': {
        'label': 'Custom Shirts', 'label_mk': 'Custom Кошули',
        'description': 'Professional dress shirts made to your exact specifications.',
        'sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'Custom'],
        'colors': ['White', 'Light Blue', 'Navy', 'Black', 'Grey', 'Cream', 'Pink', 'Lavender'],
        'materials': ['100% Cotton', 'Cotton-Polyester', 'Premium Egyptian Cotton', 'Linen', 'Oxford Cloth'],
        'icon': 'shirt'
    },
    'pants': {
        'label': 'Pants & Trousers', 'label_mk': 'Панталони',
        'description': 'Custom-fitted trousers for business and casual wear.',
        'sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'Custom'],
        'colors': ['Navy', 'Black', 'Grey', 'Khaki', 'Charcoal', 'Brown', 'Olive', 'Beige'],
        'materials': ['Wool', 'Cotton Twill', 'Polyester Blend', 'Linen', 'Corduroy'],
        'icon': 'square'
    },
    'blazers': {
        'label': 'Blazers & Suits', 'label_mk': 'Блејзери и Одела',
        'description': 'Tailored blazers and suits for the professional wardrobe.',
        'sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'Custom'],
        'colors': ['Navy', 'Black', 'Charcoal', 'Medium Grey', 'Brown', 'Burgundy', 'Olive'],
        'materials': ['100% Wool', 'Wool-Polyester', 'Premium Wool Blend', 'Tweed', 'Linen'],
        'icon': 'briefcase'
    },
    'womens': {
        'label': "Women's Apparel", 'label_mk': 'Дамска Облека',
        'description': "Dresses, blouses, skirts and professional women's wear.",
        'sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'Custom'],
        'colors': ['White', 'Black', 'Navy', 'Red', 'Pink', 'Cream', 'Grey', 'Burgundy'],
        'materials': ['Silk', 'Cotton', 'Polyester Blend', 'Linen', 'Premium Mixed'],
        'icon': 'heart'
    },
    'bags': {
        'label': 'Bags & Accessories', 'label_mk': 'Чанти и Прибор',
        'description': 'Custom bags, backpacks, and accessories for retail or corporate.',
        'sizes': ['Small', 'Medium', 'Large', 'XL', 'Custom'],
        'colors': ['Black', 'Brown', 'Navy', 'Grey', 'Tan', 'Olive', 'Burgundy', 'White'],
        'materials': ['Canvas', 'Leather', 'Polyester', 'Cotton Duck', 'Recycled Materials'],
        'icon': 'shopping-bag'
    },
    'workwear': {
        'label': 'Workwear & Uniforms', 'label_mk': 'Работна Облека',
        'description': 'Durable workwear and corporate uniforms built to last.',
        'sizes': ['XS', 'S', 'M', 'L', 'XL', 'XXL', 'XXXL', 'Custom'],
        'colors': ['Navy', 'Black', 'Grey', 'Orange', 'Yellow', 'Red', 'White', 'Khaki'],
        'materials': ['Heavy Cotton', 'Poly-Cotton Blend', 'Ripstop', 'Denim', 'Durable Water-Repellent'],
        'icon': 'hard-hat'
    },
}

SERVICES = [
    {'icon': 'scissors', 'title_key': 'svc_tailoring', 'desc_key': 'svc_tailoring_desc'},
    {'icon': 'globe', 'title_key': 'svc_export', 'desc_key': 'svc_export_desc'},
    {'icon': 'package', 'title_key': 'svc_quantity', 'desc_key': 'svc_quantity_desc'},
    {'icon': 'clock', 'title_key': 'svc_turnaround', 'desc_key': 'svc_turnaround_desc'},
    {'icon': 'award', 'title_key': 'svc_quality', 'desc_key': 'svc_quality_desc'},
    {'icon': 'message-circle', 'title_key': 'svc_communication', 'desc_key': 'svc_communication_desc'},
]

INQUIRY_STATUSES = ['New', 'Reviewed', 'Replied', 'Converted', 'Lost']


def get_products():
    """Get products from DB or fall back to hardcoded."""
    try:
        products = Product.query.filter_by(available=True).order_by(Product.sort_order).all()
        if products:
            result = {}
            for p in products:
                result[p.key] = {
                    'label': p.label, 'label_mk': p.label_mk or p.label,
                    'description': p.description,
                    'sizes': json.loads(p.available_sizes) if p.available_sizes else [],
                    'colors': json.loads(p.available_colors) if p.available_colors else [],
                    'materials': json.loads(p.available_materials) if p.available_materials else [],
                    'icon': p.icon or 'package', 'image_url': p.image_url
                }
            return result
    except Exception:
        pass
    return PRODUCTS_HARDCODED


def make_public_id():
    return str(uuid.uuid4())[:8].upper()


# ============================================================
# PUBLIC ROUTES
# ============================================================

@app.context_processor
def inject_translations():
    from translations import TRANSLATIONS, get_text
    lang = request.args.get('lang', 'en')
    if lang not in TRANSLATIONS:
        lang = 'en'
    return dict(
        t=lambda key: get_text(lang, key),
        lang=lang,
        languages=[{'code': 'en', 'label': 'EN'}, {'code': 'mk', 'label': 'MK'}]
    )


@app.route('/')
def home():
    products = get_products()
    lang = request.args.get('lang', 'en')
    return render_template('index.html', products=products, services=SERVICES, lang=lang)


@app.route('/api/inquiry', methods=['POST'])
def submit_inquiry():
    data = request.get_json()
    lang = data.get('lang', 'en')

    name = data.get('name', '').strip()
    email = data.get('email', '').strip()
    if not name or not email:
        return jsonify({'error': 'Name and email are required'}), 400

    inquiry = Inquiry(
        public_id=make_public_id(),
        company=data.get('company', '').strip(),
        contact_name=name,
        email=email,
        phone=data.get('phone', '').strip(),
        message=data.get('message', '').strip(),
        lang=lang[:2],
        status='New'
    )
    db.session.add(inquiry)
    db.session.flush()  # Get the ID

    for item in data.get('items', []):
        qi = InquiryItem(
            inquiry_id=inquiry.id,
            product_key=item.get('product_key', ''),
            product_label=item.get('product_label', ''),
            size=item.get('size', ''),
            color=item.get('color', ''),
            material=item.get('material', ''),
            quantity=int(item.get('quantity', 1))
        )
        db.session.add(qi)

    db.session.commit()

    # Send email notification
    _send_inquiry_email(inquiry, lang)

    return jsonify({'success': True, 'public_id': inquiry.public_id})


def _send_inquiry_email(inquiry, lang='en'):
    """Send email to Mimito when new inquiry arrives."""
    if not app.config['MAIL_USERNAME']:
        return

    body = f"""New Inquiry from Mimito Website

Public ID: #{inquiry.public_id}
Company: {inquiry.company or 'N/A'}
Contact: {inquiry.contact_name}
Email: {inquiry.email}
Phone: {inquiry.phone or 'N/A'}
Language: {lang.upper()}

"""
    if inquiry.items:
        body += "Configured Products:\n"
        for i, item in enumerate(inquiry.items, 1):
            body += f"\n{i}. {item.product_label}"
            body += f"\n   Size: {item.size} | Color: {item.color} | Material: {item.material}"
            body += f"\n   Quantity: {item.quantity} pcs"
    body += f"\n\nMessage:\n{inquiry.message or 'N/A'}"
    body += f"\n\n---\nMimito | #mimito-{inquiry.public_id}"

    try:
        msg = MIMEMultipart()
        msg['From'] = app.config['MAIL_USERNAME']
        msg['To'] = app.config['MAIL_USERNAME']
        msg['Subject'] = f'New Inquiry #{inquiry.public_id} from {inquiry.company or inquiry.contact_name}'
        msg.attach(MIMEText(body, 'plain'))
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
        print(f"[email] Sent inquiry #{inquiry.public_id}")
    except Exception as e:
        print(f"[email] Failed to send: {e}")


# ============================================================
# ADMIN ROUTES
# ============================================================

@app.route('/admin')
def admin():
    """Admin dashboard — list all inquiries."""
    status_filter = request.args.get('status', '')
    search = request.args.get('search', '').strip()
    sort = request.args.get('sort', 'newest')

    query = Inquiry.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search:
        query = query.filter(
            (Inquiry.contact_name.ilike(f'%{search}%')) |
            (Inquiry.company.ilike(f'%{search}%')) |
            (Inquiry.email.ilike(f'%{search}%')) |
            (Inquiry.public_id.ilike(f'%{search}%'))
        )
    if sort == 'newest':
        query = query.order_by(Inquiry.created_at.desc())
    elif sort == 'oldest':
        query = query.order_by(Inquiry.created_at.asc())
    elif sort == 'company':
        query = query.order_by(Inquiry.company.asc())
    else:
        query = query.order_by(Inquiry.created_at.desc())

    inquiries = query.all()
    stats = {
        'total': Inquiry.query.count(),
        'new': Inquiry.query.filter_by(status='New').count(),
        'reviewed': Inquiry.query.filter_by(status='Reviewed').count(),
        'converted': Inquiry.query.filter_by(status='Converted').count(),
        'lost': Inquiry.query.filter_by(status='Lost').count(),
    }
    return render_template('admin/index.html',
                           inquiries=inquiries,
                           stats=stats,
                           status_filter=status_filter,
                           search=search,
                           sort=sort,
                           statuses=INQUIRY_STATUSES)


@app.route('/admin/inquiry/<int:inquiry_id>')
def admin_inquiry_detail(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    return render_template('admin/inquiry.html', inquiry=inquiry, statuses=INQUIRY_STATUSES)


@app.route('/admin/inquiry/<int:inquiry_id>', methods=['POST'])
def admin_update_inquiry(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    inquiry.status = request.form.get('status', inquiry.status)
    inquiry.notes = request.form.get('notes', inquiry.notes)
    db.session.commit()
    return redirect(url_for('admin_inquiry_detail', inquiry_id=inquiry_id))


@app.route('/admin/inquiry/<int:inquiry_id>/delete', methods=['POST'])
def admin_delete_inquiry(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    db.session.delete(inquiry)
    db.session.commit()
    return redirect(url_for('admin'))


# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/products')
def api_products():
    return jsonify(get_products())


@app.route('/api/inquiries')
def api_inquiries():
    """API: list inquiries."""
    inquiries = Inquiry.query.order_by(Inquiry.created_at.desc()).limit(100).all()
    return jsonify([q.to_dict() for q in inquiries])


@app.route('/api/inquiry/<int:inquiry_id>/status', methods=['POST'])
def api_update_status(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    data = request.get_json()
    inquiry.status = data.get('status', inquiry.status)
    if data.get('notes'):
        inquiry.notes = data.get('notes')
    db.session.commit()
    return jsonify({'success': True})


@app.route('/api/stats')
def api_stats():
    """API: dashboard stats."""
    total = Inquiry.query.count()
    return jsonify({
        'total': total,
        'new': Inquiry.query.filter_by(status='New').count(),
        'reviewed': Inquiry.query.filter_by(status='Reviewed').count(),
        'converted': Inquiry.query.filter_by(status='Converted').count(),
        'lost': Inquiry.query.filter_by(status='Lost').count(),
        'this_week': Inquiry.query.filter(
            Inquiry.created_at >= datetime.now(tz.utc).replace(hour=0, minute=0, second=0)
        ).count()
    })


# ============================================================
# INIT
# ============================================================

def run_migrations():
    """Add missing columns to existing tables (handles schema evolution)."""
    from sqlalchemy import text
    conn = db.engine.connect()

    # Inquiry table — add missing columns
    existing = [r[0] for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='inquiries'")).fetchall()]
    migrations = [
        ("public_id", "ALTER TABLE inquiries ADD COLUMN public_id VARCHAR(12)"),
        ("status", "ALTER TABLE inquiries ADD COLUMN status VARCHAR(50) DEFAULT 'New'"),
        ("notes", "ALTER TABLE inquiries ADD COLUMN notes TEXT"),
        ("lang", "ALTER TABLE inquiries ADD COLUMN lang VARCHAR(5) DEFAULT 'en'"),
        ("updated_at", "ALTER TABLE inquiries ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"),
        ("phone", "ALTER TABLE inquiries ADD COLUMN phone VARCHAR(50)"),
    ]
    for col_name, sql in migrations:
        if col_name not in existing:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"  [migrate] Added column: {col_name}")
            except Exception as e:
                print(f"  [migrate] {col_name}: {e}")

    # InquiryItem table — add missing columns
    existing_items = [r[0] for r in conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name='inquiry_items'")).fetchall()]
    item_migrations = [
        ("notes", "ALTER TABLE inquiry_items ADD COLUMN notes TEXT"),
    ]
    for col_name, sql in item_migrations:
        if col_name not in existing_items:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"  [migrate] Added column: {col_name} (items)")
            except Exception as e:
                print(f"  [migrate] {col_name}: {e}")

    conn.close()
    print("  [migrate] Done.")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    with app.app_context():
        db.create_all()
        run_migrations()
        # Seed default products if none exist
        if Product.query.count() == 0:
            seed_products()
    print(f"\n🧵 Mimito DEV starting on port {port}...")
    print(f"   Database: {'PostgreSQL (Render)' if DATABASE_URL else 'SQLite (local)'}")
    print(f"   Admin: http://localhost:{port}/admin")
    print()
    app.run(debug=True, port=port, host='0.0.0.0')
