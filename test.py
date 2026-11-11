from app.auth.security import (
    hash_password,
    verify_password
)

password = "Employee@123"

hashed = hash_password(password)

print("Hashed password:")
print(hashed)

print("Correct password:")
print(verify_password(password, hashed))

print("Wrong password:")
print(verify_password("Wrong@123", hashed))