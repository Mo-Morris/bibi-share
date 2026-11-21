#!/usr/bin/env python3
import base64
import hashlib
import binascii


def hash_password(password_str, salt_byte):
    """使用 PBKDF2-HMAC-SHA256 加密密码"""
    dk = hashlib.pbkdf2_hmac("sha256", password_str.encode("utf-8"), salt_byte, 10000)
    return binascii.hexlify(dk)


# 给定的参数
email = "admin@yourdomain.com"
salt_base64 = "ux76nkwesWb0XWGyxB8aDQ=="

# 将 salt 从 base64 解码
salt_bytes = base64.b64decode(salt_base64)

# 输入原始密码
password = input("请输入要加密的原始密码: ")

# 加密密码
password_hashed = hash_password(password, salt_bytes)

# 转为 base64 编码（数据库中存储的格式）
password_hashed_base64 = base64.b64encode(password_hashed).decode()

print("\n" + "=" * 60)
print(f"账号邮箱: {email}")
print(f"Salt (base64): {salt_base64}")
print(f"原始密码: {password}")
print(f"加密后的密码 (base64): {password_hashed_base64}")
print("=" * 60)
