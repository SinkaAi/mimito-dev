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
from models import db, Inquiry, InquiryItem, Product, ContentBlock, ServiceBlock, SiteConfig, init_db, seed_products

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
    """Add missing columns to existing tables. Works with both SQLite (local) and PostgreSQL (Railway)."""
    from sqlalchemy import text
    try:
        conn = db.engine.connect()
        dialect = db.engine.dialect.name

        # Get existing columns — different query per dialect
        if dialect == 'postgresql':
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='inquiries'"
            ))
            existing = [r[0] for r in result.fetchall()]
        else:
            # SQLite
            result = conn.execute(text("PRAGMA table_info('inquiries')"))
            existing = [r[1] for r in result.fetchall()]

        # Migration definitions — per-dialect SQL
        migrations = [
            ("public_id", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN public_id VARCHAR(12)",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN public_id VARCHAR(12)",
            }),
            ("status", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN status VARCHAR(50) DEFAULT 'New'",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN status VARCHAR(50) DEFAULT 'New'",
            }),
            ("notes", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN notes TEXT",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN notes TEXT",
            }),
            ("lang", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN lang VARCHAR(5) DEFAULT 'en'",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN lang VARCHAR(5) DEFAULT 'en'",
            }),
            ("updated_at", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            }),
            ("phone", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN phone VARCHAR(50)",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN phone VARCHAR(50)",
            }),
        ]

        for col_name, sqls in migrations:
            if col_name not in existing:
                try:
                    conn.execute(text(sqls[dialect]))
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
    # Build content blocks dict from DB — overrides translations.py defaults
    content = {}
    try:
        for b in ContentBlock.query.all():
            content[b.block_key] = b.en_text if lang == 'en' else b.mk_text
        # Also merge SiteConfig — map internal keys to translation key names
        site_config = {c.key: c.value for c in SiteConfig.query.all()}
        # Map SiteConfig keys → translation key names used in template
        config_key_map = {
            'company_email':    'contact_email_val',
            'company_phone':    'contact_phone_val',
            'company_location':  'contact_location_val',
            'working_with':     'contact_working_val',
        }
        for db_key, display_key in config_key_map.items():
            if db_key in site_config and site_config[db_key]:
                content[display_key] = site_config[db_key]
    except Exception:
        pass  # Table might not exist yet during first migration

    def t(key):
        # DB content (ContentBlock + SiteConfig) overrides translations.py
        if key in content and content[key]:
            return content[key]
        return get_text(lang, key)

    return dict(
        t=t,
        lang=lang,
        languages=[{'code': 'en', 'label': 'EN'}, {'code': 'mk', 'label': 'MK'}],
        services_db=_get_services_db(lang),
        config_db=_get_config_db(),
    )


def _get_services_db(lang):
    """Get service blocks from DB, fallback to hardcoded."""
    try:
        blocks = ServiceBlock.query.filter_by(available=True).order_by(ServiceBlock.sort_order).all()
        if blocks:
            return [{'icon': b.icon,
                     'title_key': f'_svc_{b.id}',
                     'desc_key': f'_svcd_{b.id}',
                     '_title_en': b.title_en, '_title_mk': b.title_mk,
                     '_desc_en': b.desc_en, '_desc_mk': b.desc_mk}
                    for b in blocks]
    except Exception:
        pass
    return SERVICES


def _get_config_db():
    """Get site config from DB."""
    try:
        return {c.key: c.value for c in SiteConfig.query.all()}
    except Exception:
        return {}


# Monkey-patch the t() inside service templates — we handle services specially
@app.context_processor
def override_service_templates():
    return {}


@app.route('/')
def home():
    products = get_products()
    lang = request.args.get('lang', 'en')
    services = _get_services_db(lang)
    config = _get_config_db()
    return render_template('index.html', products=products, services_db=services, lang=lang, config_db=config)


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
    """New CMS admin panel."""
    return render_template('admin/cms.html')


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


# ─── Content Blocks API ────────────────────────────────────────────────────────

@app.route('/api/content')
def api_content_list():
    """GET all content blocks. Returns {} fallback for missing keys."""
    blocks = {b.block_key: b for b in ContentBlock.query.all()}
    return jsonify({k: v.to_dict() for k, v in blocks.items()})


@app.route('/api/content/<key>')
def api_content_get(key):
    block = ContentBlock.query.filter_by(block_key=key).first()
    if not block:
        return jsonify({'block_key': key, 'en_text': '', 'mk_text': ''})
    return jsonify(block.to_dict())


@app.route('/api/content/<key>', methods=['PUT'])
def api_content_put(key):
    """Create or update a content block."""
    data = request.get_json()
    block = ContentBlock.query.filter_by(block_key=key).first()
    if block:
        block.en_text = data.get('en_text', block.en_text)
        block.mk_text = data.get('mk_text', block.mk_text)
    else:
        block = ContentBlock(
            block_key=key,
            en_text=data.get('en_text', ''),
            mk_text=data.get('mk_text', '')
        )
        db.session.add(block)
    db.session.commit()
    return jsonify(block.to_dict())


@app.route('/api/content/bulk', methods=['PUT'])
def api_content_bulk():
    """Bulk update multiple content blocks at once."""
    data = request.get_json()
    updated = []
    for key, vals in data.items():
        block = ContentBlock.query.filter_by(block_key=key).first()
        if block:
            if 'en_text' in vals:
                block.en_text = vals['en_text']
            if 'mk_text' in vals:
                block.mk_text = vals['mk_text']
        else:
            block = ContentBlock(
                block_key=key,
                en_text=vals.get('en_text', ''),
                mk_text=vals.get('mk_text', '')
            )
            db.session.add(block)
        updated.append(key)
    db.session.commit()
    return jsonify({'updated': updated})


# ─── Service Blocks API ───────────────────────────────────────────────────────

@app.route('/api/services')
def api_services_list():
    blocks = ServiceBlock.query.order_by(ServiceBlock.sort_order).all()
    if not blocks:
        # Fallback to hardcoded SERVICES
        return jsonify(SERVICES_FALLBACK)
    return jsonify([b.to_dict() for b in blocks])


@app.route('/api/services', methods=['POST'])
def api_services_create():
    data = request.get_json()
    block = ServiceBlock(
        icon=data.get('icon', 'package'),
        title_en=data.get('title_en', ''),
        title_mk=data.get('title_mk', ''),
        desc_en=data.get('desc_en', ''),
        desc_mk=data.get('desc_mk', ''),
        sort_order=data.get('sort_order', 0),
    )
    db.session.add(block)
    db.session.commit()
    return jsonify(block.to_dict())


@app.route('/api/services/<int:block_id>', methods=['PUT'])
def api_services_update(block_id):
    block = ServiceBlock.query.get_or_404(block_id)
    data = request.get_json()
    block.icon = data.get('icon', block.icon)
    block.title_en = data.get('title_en', block.title_en)
    block.title_mk = data.get('title_mk', block.title_mk)
    block.desc_en = data.get('desc_en', block.desc_en)
    block.desc_mk = data.get('desc_mk', block.desc_mk)
    block.sort_order = data.get('sort_order', block.sort_order)
    block.available = data.get('available', block.available)
    db.session.commit()
    return jsonify(block.to_dict())


@app.route('/api/services/<int:block_id>', methods=['DELETE'])
def api_services_delete(block_id):
    block = ServiceBlock.query.get_or_404(block_id)
    db.session.delete(block)
    db.session.commit()
    return jsonify({'deleted': True})


# ─── Site Config API ───────────────────────────────────────────────────────────

@app.route('/api/config')
def api_config_list():
    configs = {c.key: c.value for c in SiteConfig.query.all()}
    # Always include defaults
    defaults = {
        'company_email': 'info@mimito.com',
        'company_phone': '+389 XX XXX XXXX',
        'company_location': 'Štip, North Macedonia',
        'working_with': 'Germany · EU · Worldwide',
    }
    defaults.update(configs)
    return jsonify(defaults)


@app.route('/api/config/<key>', methods=['PUT'])
def api_config_put(key):
    config = SiteConfig.query.filter_by(key=key).first()
    if config:
        config.value = request.get_json().get('value', config.value)
    else:
        config = SiteConfig(key=key, value=request.get_json().get('value', ''))
        db.session.add(config)
    db.session.commit()
    return jsonify(config.to_dict())


SERVICES_FALLBACK = [
    {'icon': 'scissors', 'title_en': 'Custom Tailoring', 'title_mk': 'Custom Шиење',
     'desc_en': 'Every garment made to your exact measurements and specifications.',
     'desc_mk': 'Секое парче облека изработено според вашите точни мерки и спецификации.',
     'sort_order': 0},
    {'icon': 'globe', 'title_en': 'EU Export Ready', 'title_mk': 'Подготвено за ЕУ',
     'desc_en': 'Years of experience exporting quality garments to Germany and the EU.',
     'desc_mk': 'Години искуство во извоз на квалитетна облека во Германија и ЕУ.',
     'sort_order': 1},
    {'icon': 'package', 'title_en': 'Any Quantity', 'title_mk': 'Било каква Количина',
     'desc_en': 'Flexible MOQ — from small batches to large-scale production runs.',
     'desc_mk': 'Флексибилен МОК — од мали серии до големи производствени капацитети.',
     'sort_order': 2},
    {'icon': 'clock', 'title_en': 'Fast Turnaround', 'title_mk': 'Брза Испорака',
     'desc_en': 'Reliable production timelines with clear milestones and updates.',
     'desc_mk': 'Сигурни производствени рокови со јасни милстоуни и ажурирања.',
     'sort_order': 3},
    {'icon': 'award', 'title_en': 'Quality Materials', 'title_mk': 'Квалитетни Материјали',
     'desc_en': 'Premium fabrics sourced from trusted European suppliers.',
     'desc_mk': 'Премиум ткаенини од доверени европски добавувачи.',
     'sort_order': 4},
    {'icon': 'message-circle', 'title_en': 'Direct Communication', 'title_mk': 'Директна Комуникација',
     'desc_en': 'Personal point of contact throughout the entire production process.',
     'desc_mk': 'Личен контакт во текот на целиот производствен процес.',
     'sort_order': 5},
]


# ============================================================
# INIT
# ============================================================

def run_migrations():
    """Add missing columns to existing tables. Works with both SQLite (local) and PostgreSQL (Railway)."""
    from sqlalchemy import text
    try:
        conn = db.engine.connect()
        dialect = db.engine.dialect.name

        # Get existing columns — different query per dialect
        if dialect == 'postgresql':
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='inquiries'"
            ))
            existing = [r[0] for r in result.fetchall()]
            result_items = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name='inquiry_items'"
            ))
            existing_items = [r[0] for r in result_items.fetchall()]
        else:
            # SQLite
            result = conn.execute(text("PRAGMA table_info('inquiries')"))
            existing = [r[1] for r in result.fetchall()]
            result_items = conn.execute(text("PRAGMA table_info('inquiry_items')"))
            existing_items = [r[1] for r in result_items.fetchall()]

        # Inquiry table migrations
        migrations = [
            ("public_id", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN public_id VARCHAR(12)",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN public_id VARCHAR(12)",
            }),
            ("status", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN status VARCHAR(50) DEFAULT 'New'",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN status VARCHAR(50) DEFAULT 'New'",
            }),
            ("notes", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN notes TEXT",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN notes TEXT",
            }),
            ("lang", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN lang VARCHAR(5) DEFAULT 'en'",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN lang VARCHAR(5) DEFAULT 'en'",
            }),
            ("updated_at", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP",
            }),
            ("phone", {
                "postgresql": "ALTER TABLE inquiries ADD COLUMN phone VARCHAR(50)",
                "sqlite":     "ALTER TABLE inquiries ADD COLUMN phone VARCHAR(50)",
            }),
        ]
        for col_name, sqls in migrations:
            if col_name not in existing:
                try:
                    conn.execute(text(sqls[dialect]))
                    conn.commit()
                    print(f"  [migrate] added: {col_name}")
                except Exception as e:
                    print(f"  [migrate] {col_name}: {e}")

        # InquiryItem table migrations
        item_migrations = [("notes", {
            "postgresql": "ALTER TABLE inquiry_items ADD COLUMN notes TEXT",
            "sqlite":     "ALTER TABLE inquiry_items ADD COLUMN notes TEXT",
        })]
        for col_name, sqls in item_migrations:
            if col_name not in existing_items:
                try:
                    conn.execute(text(sqls[dialect]))
                    conn.commit()
                    print(f"  [migrate] added: {col_name} (items)")
                except Exception as e:
                    print(f"  [migrate] {col_name}: {e}")

        conn.close()
        print("  [migrate] Done.")
    except Exception as e:
        print(f"  [migrate] error: {e}")


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
