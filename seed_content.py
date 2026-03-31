"""
Seed content blocks from existing translations.py into the DB.
Run once to populate the CMS with all existing content.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app import app, db, ContentBlock
from translations import TRANSLATIONS

def seed_content():
    all_keys = set()
    for lang_data in TRANSLATIONS.values():
        all_keys.update(lang_data.keys())

    existing = {b.block_key: b for b in ContentBlock.query.all()}
    count = 0
    for key in sorted(all_keys):
        if key in existing:
            continue
        en_val = TRANSLATIONS['en'].get(key, '')
        mk_val = TRANSLATIONS['mk'].get(key, '')
        block = ContentBlock(block_key=key, en_text=en_val, mk_text=mk_val)
        db.session.add(block)
        count += 1

    db.session.commit()
    print(f"Seeded {count} content blocks from translations.py")

def seed_services():
    """Seed service blocks from hardcoded SERVICES list."""
    from app import SERVICES_FALLBACK
    existing = ServiceBlock.query.count()
    if existing > 0:
        print(f"Service blocks already exist ({existing}), skipping")
        return
    for s in SERVICES_FALLBACK:
        block = ServiceBlock(
            icon=s['icon'],
            title_en=s['title_en'],
            title_mk=s['title_mk'],
            desc_en=s['desc_en'],
            desc_mk=s['desc_mk'],
            sort_order=s['sort_order'],
        )
        db.session.add(block)
    db.session.commit()
    print(f"Seeded {len(SERVICES_FALLBACK)} service blocks")

if __name__ == '__main__':
    with app.app_context():
        from models import ServiceBlock
        seed_content()
        seed_services()
