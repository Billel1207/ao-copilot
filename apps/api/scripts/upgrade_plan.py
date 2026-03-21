"""Script admin — Met à jour le plan d'une organisation vers Business.

Usage: python scripts/upgrade_plan.py billel_abbas@yahoo.fr business
"""
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SyncSessionLocal
from app.models.user import User
from app.models.organization import Organization


def upgrade_plan(email: str, plan: str = "business"):
    db = SyncSessionLocal()
    try:
        user = db.query(User).filter_by(email=email.lower()).first()
        if not user:
            print(f"❌ Utilisateur '{email}' non trouvé")
            return False

        org = db.query(Organization).filter_by(id=user.org_id).first()
        if not org:
            print(f"❌ Organisation non trouvée pour {email}")
            return False

        old_plan = org.plan
        org.plan = plan
        org.quota_docs = 99999  # Illimité pour Business
        db.commit()
        print(f"✅ {org.name} — plan mis à jour : {old_plan} → {plan}")
        print(f"   Quota docs : 99999 (illimité)")
        print(f"   Utilisateur : {user.email}")
        return True
    finally:
        db.close()


if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "billel_abbas@yahoo.fr"
    plan = sys.argv[2] if len(sys.argv) > 2 else "business"
    upgrade_plan(email, plan)
