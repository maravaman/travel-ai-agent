#!/usr/bin/env python3

import jwt
import secrets
from datetime import datetime, timedelta

def test_jwt_generation():
    """Test JWT token generation"""
    # Generate secret
    jwt_secret = secrets.token_urlsafe(32)
    print(f"JWT Secret: {jwt_secret}")
    
    # Create payload
    payload = {
        'user_id': 1007,
        'username': 'testuser456',
        'exp': datetime.utcnow() + timedelta(hours=24),
        'iat': datetime.utcnow()
    }
    print(f"Payload: {payload}")
    
    # Generate token
    try:
        token = jwt.encode(payload, jwt_secret, algorithm='HS256')
        print(f"Generated Token: {token}")
        print(f"Token Length: {len(token)}")
        print(f"Token Type: {type(token)}")
        
        # Verify token
        decoded = jwt.decode(token, jwt_secret, algorithms=['HS256'])
        print(f"Decoded Payload: {decoded}")
        
        return token
    except Exception as e:
        print(f"JWT Error: {e}")
        return None

if __name__ == "__main__":
    test_jwt_generation()
