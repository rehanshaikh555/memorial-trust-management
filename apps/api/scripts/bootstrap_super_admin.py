from getpass import getpass

from sqlalchemy import select

from app.db.session import SessionLocal
from app.core.security import hash_password
from app.models.role import Role
from app.models.user import User


def main() -> None:
    print("================================================")
    print("MEMORIAL TRUST MANAGEMENT")
    print("SUPER ADMIN BOOTSTRAP")
    print("================================================")
    print()

    email = input("Admin email: ").strip().lower()
    full_name = input("Admin full name: ").strip()

    if not email:
        raise ValueError("Admin email is required.")

    if not full_name:
        raise ValueError("Admin full name is required.")

    password = getpass("Admin password: ")
    password_confirm = getpass("Confirm password: ")

    if not password:
        raise ValueError("Admin password is required.")

    if password != password_confirm:
        raise ValueError("Passwords do not match.")

    if len(password) < 12:
        raise ValueError(
            "Admin password must contain at least 12 characters."
        )

    db = SessionLocal()

    try:
        existing_user = db.scalar(
            select(User).where(User.email == email)
        )

        if existing_user is not None:
            raise RuntimeError(
                "A user with this email already exists. "
                "Bootstrap will not overwrite existing accounts."
            )

        role = db.scalar(
            select(Role).where(Role.name == "SUPER_ADMIN")
        )

        if role is None:
            raise RuntimeError(
                "SUPER_ADMIN role does not exist. "
                "Run the RBAC seed migration first."
            )

        user = User(
            email=email,
            password_hash=hash_password(password),
            full_name=full_name,
            role_id=role.id,
            trust_id=None,
            is_active=True,
            is_verified=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print()
        print("================================================")
        print("SUPER ADMIN CREATED")
        print("================================================")
        print("User ID :", user.id)
        print("Email   :", user.email)
        print("Name    :", user.full_name)
        print("Role    :", role.name)
        print("Active  :", user.is_active)
        print("Verified:", user.is_verified)
        print()
        print("Password was not stored or displayed.")
        print("================================================")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    main()
