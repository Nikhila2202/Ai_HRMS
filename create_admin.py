from database import SessionLocal
from app.models.model import Employee, User, Role, UserRole
from app.auth.security import hash_password

db = SessionLocal()

try:
    employee = db.query(Employee).filter(
        Employee.employee_id == 1
    ).first()

    if not employee:
        raise Exception("Employee ID 1 not found")

    admin_role = db.query(Role).filter(
        Role.role_name == "Admin"
    ).first()

    if not admin_role:
        raise Exception("Admin role not found")

    user = db.query(User).filter(
        User.employee_id == employee.employee_id
    ).first()

    if not user:
        user = User(
            employee_id=employee.employee_id,
            email=employee.email,
            password_hash=hash_password("Admin@12345"),
            is_active=True
        )
        db.add(user)
        db.flush()

    existing_role = db.query(UserRole).filter(
        UserRole.user_id == user.user_id,
        UserRole.role_id == admin_role.role_id
    ).first()

    if not existing_role:
        db.add(UserRole(
            user_id=user.user_id,
            role_id=admin_role.role_id
        ))

    db.commit()

    print("Admin account created/verified")
    print("Email:", user.email)
    print("Temporary password: Admin@12345")

except Exception:
    db.rollback()
    raise

finally:
    db.close()