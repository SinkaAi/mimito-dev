"""
Mimito Dev — Tests
Run with: pytest tests/ -v
"""
import pytest
import sys
import os

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db


@pytest.fixture
def client():
    """Create a test client with a temporary database."""
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()


@pytest.fixture
def app_context():
    with app.app_context():
        db.create_all()
        yield
        db.drop_all()


# ============================================================
# PUBLIC ROUTES
# ============================================================

def test_homepage_loads(client):
    """Homepage should return 200."""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Mimito' in rv.data


def test_homepage_macedonian(client):
    """Macedonian version should load."""
    rv = client.get('/?lang=mk')
    assert rv.status_code == 200


def test_products_api(client):
    """Products API should return JSON with product keys."""
    rv = client.get('/api/products')
    assert rv.status_code == 200
    data = rv.get_json()
    assert 'shirts' in data
    assert 'blazers' in data
    assert 'pants' in data


# ============================================================
# INQUIRY API
# ============================================================

def test_submit_inquiry_success(client, app_context):
    """Valid inquiry should be stored in DB."""
    from models import Inquiry, InquiryItem

    payload = {
        'name': 'John Doe',
        'email': 'john@example.com',
        'company': 'Test Corp',
        'phone': '+123456',
        'message': 'I need custom shirts',
        'items': [
            {
                'product_key': 'shirts',
                'product_label': 'Custom Shirts',
                'size': 'M',
                'color': 'Navy',
                'material': '100% Cotton',
                'quantity': 50
            }
        ]
    }

    rv = client.post('/api/inquiry',
                     json=payload,
                     content_type='application/json')
    assert rv.status_code == 200
    data = rv.get_json()
    assert data['success'] is True
    assert 'public_id' in data

    # Verify stored in DB
    inquiry = Inquiry.query.filter_by(public_id=data['public_id']).first()
    assert inquiry is not None
    assert inquiry.contact_name == 'John Doe'
    assert inquiry.company == 'Test Corp'
    assert inquiry.email == 'john@example.com'
    assert len(inquiry.items) == 1
    assert inquiry.items[0].product_key == 'shirts'
    assert inquiry.items[0].quantity == 50


def test_submit_inquiry_missing_name(client, app_context):
    """Missing name should return 400."""
    rv = client.post('/api/inquiry',
                     json={'email': 'test@test.com'},
                     content_type='application/json')
    assert rv.status_code == 400


def test_submit_inquiry_missing_email(client, app_context):
    """Missing email should return 400."""
    rv = client.post('/api/inquiry',
                     json={'name': 'Test'},
                     content_type='application/json')
    assert rv.status_code == 400


def test_submit_inquiry_multiple_items(client, app_context):
    """Inquiry with multiple products should store all items."""
    from models import Inquiry, InquiryItem

    payload = {
        'name': 'Jane Doe',
        'email': 'jane@example.com',
        'items': [
            {'product_key': 'shirts', 'product_label': 'Custom Shirts', 'size': 'S', 'color': 'White', 'material': 'Cotton', 'quantity': 30},
            {'product_key': 'pants', 'product_label': 'Pants', 'size': 'M', 'color': 'Navy', 'material': 'Wool', 'quantity': 20},
            {'product_key': 'blazers', 'product_label': 'Blazers', 'size': 'L', 'color': 'Black', 'material': 'Wool', 'quantity': 10},
        ]
    }

    rv = client.post('/api/inquiry', json=payload)
    assert rv.status_code == 200

    inquiry = Inquiry.query.filter_by(email='jane@example.com').first()
    assert len(inquiry.items) == 3
    total_qty = sum(item.quantity for item in inquiry.items)
    assert total_qty == 60


def test_submit_inquiry_empty_items(client, app_context):
    """Inquiry with no items should still be stored."""
    from models import Inquiry

    payload = {
        'name': 'Solo Contact',
        'email': 'solo@example.com',
        'message': 'Just asking about pricing'
    }
    rv = client.post('/api/inquiry', json=payload)
    assert rv.status_code == 200
    inquiry = Inquiry.query.filter_by(email='solo@example.com').first()
    assert inquiry is not None
    assert len(inquiry.items) == 0


# ============================================================
# ADMIN ROUTES
# ============================================================

def test_admin_loads(client):
    """Admin page should load."""
    rv = client.get('/admin')
    assert rv.status_code == 200


def test_admin_inquiry_list(client, app_context):
    """Admin should show submitted inquiries."""
    # Submit an inquiry first
    client.post('/api/inquiry', json={'name': 'Admin Test', 'email': 'admin@test.com'})
    rv = client.get('/admin')
    assert rv.status_code == 200
    assert b'Admin Test' in rv.data


def test_admin_stats_api(client, app_context):
    """Stats API should return correct counts."""
    # Add some inquiries
    for i in range(3):
        client.post('/api/inquiry', json={'name': f'User {i}', 'email': f'user{i}@test.com'})

    rv = client.get('/api/stats')
    data = rv.get_json()
    assert data['total'] == 3
    assert data['new'] == 3


def test_admin_inquiry_detail(client, app_context):
    """Admin detail page should show full inquiry."""
    from models import Inquiry

    # Submit
    r = client.post('/api/inquiry', json={'name': 'Detail Test', 'email': 'detail@test.com', 'company': 'Detail Co', 'message': 'Test message'})
    public_id = r.get_json()['public_id']
    inquiry = Inquiry.query.filter_by(public_id=public_id).first()

    rv = client.get(f'/admin/inquiry/{inquiry.id}')
    assert rv.status_code == 200
    assert b'Detail Test' in rv.data
    assert b'Detail Co' in rv.data
    assert b'Test message' in rv.data


def test_admin_update_status(client, app_context):
    """Admin should be able to update inquiry status."""
    from models import Inquiry

    r = client.post('/api/inquiry', json={'name': 'Status Test', 'email': 'status@test.com'})
    public_id = r.get_json()['public_id']
    inquiry = Inquiry.query.filter_by(public_id=public_id).first()

    rv = client.post(f'/admin/inquiry/{inquiry.id}',
                     data={'status': 'Reviewed', 'notes': 'Looks good'},
                     content_type='application/x-www-form-urlencoded',
                     follow_redirects=False)
    assert rv.status_code in [200, 302]

    updated = db.session.get(Inquiry,inquiry.id)
    assert updated.status == 'Reviewed'
    assert updated.notes == 'Looks good'


def test_admin_delete_inquiry(client, app_context):
    """Admin should be able to delete an inquiry."""
    from models import Inquiry

    r = client.post('/api/inquiry', json={'name': 'Delete Me', 'email': 'delete@test.com'})
    public_id = r.get_json()['public_id']
    inquiry = Inquiry.query.filter_by(public_id=public_id).first()
    inquiry_id = inquiry.id

    rv = client.post(f'/admin/inquiry/{inquiry_id}/delete',
                     content_type='application/x-www-form-urlencoded')
    assert rv.status_code in [200, 302]
    assert db.session.get(Inquiry,inquiry_id) is None


def test_admin_filter_by_status(client, app_context):
    """Admin should filter by status."""
    # Add inquiries
    r = client.post('/api/inquiry', json={'name': 'New Guy', 'email': 'new@test.com'})
    public_id = r.get_json()['public_id']

    # Change one to Reviewed
    from models import Inquiry
    inquiry = Inquiry.query.filter_by(public_id=public_id).first()
    inquiry.status = 'Reviewed'
    inquiry.notes = 'test'
    from app import db as _db
    _db.session.commit()

    rv = client.get('/admin?status=Reviewed')
    assert rv.status_code == 200
    assert b'New Guy' in rv.data

    rv2 = client.get('/admin?status=New')
    assert rv2.status_code == 200
    assert b'New Guy' not in rv2.data


def test_admin_search(client, app_context):
    """Admin search should filter correctly."""
    client.post('/api/inquiry', json={'name': 'Searchable Person', 'email': 'search@test.com', 'company': 'Big Corp'})

    rv = client.get('/admin?search=Big+Corp')
    assert rv.status_code == 200
    assert b'Searchable Person' in rv.data

    rv2 = client.get('/admin?search=nonexistent')
    assert rv2.status_code == 200
    assert b'Searchable Person' not in rv2.data
