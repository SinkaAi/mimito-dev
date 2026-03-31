"""
Mimito Dev — Database Models
SQLAlchemy with PostgreSQL (Render) + SQLite fallback for local dev
"""
import os
from datetime import datetime, timezone as tz
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Database URL: use PostgreSQL on Render, SQLite locally
DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL and DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)

SQLALCHEMY_DATABASE_URI = DATABASE_URL or 'sqlite:///mimito.db'
SQLALCHEMY_TRACK_MODIFICATIONS = False


class Inquiry(db.Model):
    """An inquiry submission from a potential client."""
    __tablename__ = 'inquiries'

    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(12), unique=True, nullable=False)
    company = db.Column(db.String(200))
    contact_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(50))
    message = db.Column(db.Text)
    status = db.Column(db.String(50), default='New')  # New, Reviewed, Replied, Converted, Lost
    notes = db.Column(db.Text)  # Internal notes
    lang = db.Column(db.String(5), default='en')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    items = db.relationship('InquiryItem', backref='inquiry', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'public_id': self.public_id,
            'company': self.company,
            'contact_name': self.contact_name,
            'email': self.email,
            'phone': self.phone,
            'message': self.message,
            'status': self.status,
            'notes': self.notes,
            'lang': self.lang,
            'items': [item.to_dict() for item in self.items],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class InquiryItem(db.Model):
    """A configured product inside an inquiry."""
    __tablename__ = 'inquiry_items'

    id = db.Column(db.Integer, primary_key=True)
    inquiry_id = db.Column(db.Integer, db.ForeignKey('inquiries.id'), nullable=False)
    product_key = db.Column(db.String(50), nullable=False)  # e.g. 'shirts', 'blazers'
    product_label = db.Column(db.String(200), nullable=False)  # Display name
    size = db.Column(db.String(20), nullable=False)
    color = db.Column(db.String(50), nullable=False)
    material = db.Column(db.String(200), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'product_key': self.product_key,
            'product_label': self.product_label,
            'size': self.size,
            'color': self.color,
            'material': self.material,
            'quantity': self.quantity,
            'notes': self.notes,
        }


class Product(db.Model):
    """A product category."""
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)  # 'shirts', 'blazers'
    label = db.Column(db.String(200), nullable=False)
    label_mk = db.Column(db.String(200))  # Macedonian
    description = db.Column(db.Text)
    description_mk = db.Column(db.Text)
    icon = db.Column(db.String(50), default='package')
    image_url = db.Column(db.String(500))  # URL to product image
    available_sizes = db.Column(db.Text)  # JSON string of sizes
    available_colors = db.Column(db.Text)  # JSON string of colors
    available_materials = db.Column(db.Text)  # JSON string of materials
    available = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'label': self.label,
            'label_mk': self.label_mk,
            'description': self.description,
            'description_mk': self.description_mk,
            'icon': self.icon,
            'image_url': self.image_url,
            'available_sizes': self.available_sizes,
            'available_colors': self.available_colors,
            'available_materials': self.available_materials,
            'available': self.available,
            'sort_order': self.sort_order,
        }


def init_db(app):
    """Initialize database with app context."""
    db.init_app(app)
    with app.app_context():
        db.create_all()
        # Seed default products if none exist
        if Product.query.count() == 0:
            seed_products()


def seed_products():
    """Seed default product categories."""
    products = [
        Product(key='shirts', label='Custom Shirts', label_mk='Custom Кошули',
                description='Professional dress shirts made to your exact specifications.',
                description_mk='Професионални кошули изработени според вашите точни спецификации.',
                icon='shirt', available_sizes='["XS","S","M","L","XL","XXL","Custom"]',
                available_colors='["White","Light Blue","Navy","Black","Grey","Cream","Pink","Lavender"]',
                available_materials='["100% Cotton","Cotton-Polyester","Premium Egyptian Cotton","Linen","Oxford Cloth"]',
                sort_order=1),
        Product(key='pants', label='Pants & Trousers', label_mk='Панталони',
                description='Custom-fitted trousers for business and casual wear.',
                description_mk='Панталони изработени по мерка за бизнис и секојдневна облека.',
                icon='square', available_sizes='["XS","S","M","L","XL","XXL","Custom"]',
                available_colors='["Navy","Black","Grey","Khaki","Charcoal","Brown","Olive","Beige"]',
                available_materials='["Wool","Cotton Twill","Polyester Blend","Linen","Corduroy"]',
                sort_order=2),
        Product(key='blazers', label='Blazers & Suits', label_mk='Блејзери и Одела',
                description='Tailored blazers and suits for the professional wardrobe.',
                description_mk='Совршени блејзери и одела за професионална гардероба.',
                icon='briefcase', available_sizes='["XS","S","M","L","XL","XXL","Custom"]',
                available_colors='["Navy","Black","Charcoal","Medium Grey","Brown","Burgundy","Olive"]',
                available_materials='["100% Wool","Wool-Polyester","Premium Wool Blend","Tweed","Linen"]',
                sort_order=3),
        Product(key='womens', label="Women's Apparel", label_mk='Дамска Облека',
                description="Dresses, blouses, skirts and professional women's wear.",
                description_mk='Фустани, блузи, здолништа и професионална дамска облека.',
                icon='heart', available_sizes='["XS","S","M","L","XL","XXL","Custom"]',
                available_colors='["White","Black","Navy","Red","Pink","Cream","Grey","Burgundy"]',
                available_materials='["Silk","Cotton","Polyester Blend","Linen","Premium Mixed"]',
                sort_order=4),
        Product(key='bags', label='Bags & Accessories', label_mk='Чанти и Прибор',
                description='Custom bags, backpacks, and accessories for retail or corporate.',
                description_mk='Custom чанти, ранци и прибор за малопродажба или корпоратив.',
                icon='shopping-bag', available_sizes='["Small","Medium","Large","XL","Custom"]',
                available_colors='["Black","Brown","Navy","Grey","Tan","Olive","Burgundy","White"]',
                available_materials='["Canvas","Leather","Polyester","Cotton Duck","Recycled Materials"]',
                sort_order=5),
        Product(key='workwear', label='Workwear & Uniforms', label_mk='Работна Облека',
                description='Durable workwear and corporate uniforms built to last.',
                description_mk='Издржлива работна облека и корпоративни униформи.',
                icon='hard-hat', available_sizes='["XS","S","M","L","XL","XXL","XXXL","Custom"]',
                available_colors='["Navy","Black","Grey","Orange","Yellow","Red","White","Khaki"]',
                available_materials='["Heavy Cotton","Poly-Cotton Blend","Ripstop","Denim","Durable Water-Repellent"]',
                sort_order=6),
    ]
    for p in products:
        db.session.add(p)
    db.session.commit()
    print("[db] Seeded 6 default products")


# ─── Content Blocks (CMS) ─────────────────────────────────────────────────────

class ContentBlock(db.Model):
    """Editable translatable text content for the site."""
    __tablename__ = 'content_blocks'

    id = db.Column(db.Integer, primary_key=True)
    block_key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    en_text = db.Column(db.Text, default='')
    mk_text = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'block_key': self.block_key,
            'en_text': self.en_text,
            'mk_text': self.mk_text,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }


class ServiceBlock(db.Model):
    """Editable service cards."""
    __tablename__ = 'service_blocks'

    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(50), default='package')
    title_en = db.Column(db.String(200), nullable=False)
    title_mk = db.Column(db.String(200), default='')
    desc_en = db.Column(db.Text, default='')
    desc_mk = db.Column(db.Text, default='')
    sort_order = db.Column(db.Integer, default=0)
    available = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'icon': self.icon,
            'title_en': self.title_en,
            'title_mk': self.title_mk,
            'desc_en': self.desc_en,
            'desc_mk': self.desc_mk,
            'sort_order': self.sort_order,
            'available': self.available,
        }


class SiteConfig(db.Model):
    """Non-translatable site settings."""
    __tablename__ = 'site_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, default='')
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
