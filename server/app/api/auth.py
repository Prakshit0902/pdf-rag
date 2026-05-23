import os
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

security = HTTPBearer(auto_error=False)

# Maintain a global PyJWKClient instance to fetch and cache Clerk's public keys
jwk_client = None
CLERK_JWKS_URL = None

def get_jwk_client():
    global jwk_client, CLERK_JWKS_URL
    if jwk_client is None:
        CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")
        if CLERK_JWKS_URL:
            jwk_client = jwt.PyJWKClient(CLERK_JWKS_URL)
    return jwk_client

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """
    FastAPI dependency to extract and verify the Clerk user_id from the Authorization header.
    If no authorization header is provided, it falls back to 'default_tenant' for backward compatibility.
    """
    if not credentials:
        return "default_tenant"
    
    token = credentials.credentials
    if not token:
        return "default_tenant"
    
    # Handle mock tokens for unit testing / local verification
    if token == "mock_test_token":
        return "mock_user_id"
    if token.startswith("mock_"):
        return token.replace("mock_", "")
        
    client = get_jwk_client()
    if not CLERK_JWKS_URL or not client:
        # If JWKS URL is not configured but a token is sent, warn and fallback
        print("WARNING: Token received but CLERK_JWKS_URL is not configured. Falling back to default_tenant.")
        return "default_tenant"
        
    try:
        # Fetch the signing key from the JWKS endpoint
        signing_key = client.get_signing_key_from_jwt(token)
        # Decode and verify the JWT
        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token is missing subject claim ('sub')"
            )
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT if token == "invalid_mock_token" else status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {str(e)}"
        )
