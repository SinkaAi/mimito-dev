# Gunicorn config for Mimito Dev
import app as mimito_app

def post_fork(server, worker):
    """Run once per forked worker, with mutex so only first worker does migration."""
    import os
    lock_file = '/tmp/mimito_migrations.lock'
    if os.path.exists(lock_file):
        return
    try:
        with mimito_app.app.app_context():
            mimito_app._do_migrations()
        open(lock_file, 'w').close()
    except Exception as e:
        print(f"  [migrate] worker error: {e}")
