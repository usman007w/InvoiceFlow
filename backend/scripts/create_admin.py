import getpass
import sys

from sqlalchemy import select

from app.core.security import hash_password
from app.db import Company, SessionLocal, User, init_db


def main():
    if len(sys.argv) != 3:
        print('Usage: python -m scripts.create_admin "Company Name" email')
        return
    company_name = sys.argv[1]
    email = sys.argv[2].strip().lower()
    password = getpass.getpass("Password (12+ characters): ")
    if len(password) < 12 or password != getpass.getpass("Repeat password: "):
        print("Password too short or does not match")
        return
    init_db()
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            print("User already exists")
            return
        company = db.scalar(select(Company).where(Company.name == company_name))
        if company is None:
            company = Company(name=company_name)
            db.add(company)
            db.commit()
            db.refresh(company)
        db.add(User(email=email, password_hash=hash_password(password), role="admin", company_id=company.id))
        db.commit()
    print(f"Admin {email} created for {company_name}")


main()