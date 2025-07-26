from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import load_pem_private_key, load_pem_public_key
import os
import json
import uuid
import logging
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection for auth
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

logger = logging.getLogger(__name__)

# Security configuration
CERTIFICATE_ALGORITHM = "RS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

security = HTTPBearer()

class CertificateManager:
    def __init__(self):
        # Generate or load master key pair for signing certificates
        self.private_key, self.public_key = self._get_or_create_master_keys()
    
    def _get_or_create_master_keys(self):
        """Generate or load master RSA key pair for certificate signing"""
        private_key_path = ROOT_DIR / "master_private.pem"
        public_key_path = ROOT_DIR / "master_public.pem"
        
        try:
            # Try to load existing keys
            if private_key_path.exists() and public_key_path.exists():
                with open(private_key_path, "rb") as f:
                    private_key = load_pem_private_key(f.read(), password=None)
                with open(public_key_path, "rb") as f:
                    public_key = load_pem_public_key(f.read())
                logger.info("Loaded existing master keys")
                return private_key, public_key
        except Exception as e:
            logger.warning(f"Could not load existing keys: {e}")
        
        # Generate new key pair
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        public_key = private_key.public_key()
        
        # Save keys to files
        try:
            with open(private_key_path, "wb") as f:
                f.write(private_key.private_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PrivateFormat.PKCS8,
                    encryption_algorithm=serialization.NoEncryption()
                ))
            
            with open(public_key_path, "wb") as f:
                f.write(public_key.public_bytes(
                    encoding=serialization.Encoding.PEM,
                    format=serialization.PublicFormat.SubjectPublicKeyInfo
                ))
            logger.info("Generated and saved new master keys")
        except Exception as e:
            logger.error(f"Could not save keys: {e}")
        
        return private_key, public_key
    
    async def generate_client_certificate(self, client_name: str, client_email: str, 
                                        expires_days: int = 365) -> dict:
        """Generate a signed certificate for a client"""
        try:
            certificate_id = str(uuid.uuid4())
            issued_at = datetime.utcnow()
            expires_at = issued_at + timedelta(days=expires_days)
            
            # Certificate payload
            certificate_data = {
                "certificate_id": certificate_id,
                "client_name": client_name,
                "client_email": client_email,
                "issued_at": issued_at.isoformat(),
                "expires_at": expires_at.isoformat(),
                "issuer": "Joinery Project Manager",
                "permissions": ["project_access", "financial_view"]
            }
            
            # Sign the certificate using RSA private key
            private_key_pem = self.private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
            
            signed_certificate = jwt.encode(
                certificate_data, 
                private_key_pem, 
                algorithm=CERTIFICATE_ALGORITHM
            )
            
            # Store certificate info in database
            await db.certificates.insert_one({
                "certificate_id": certificate_id,
                "client_name": client_name,
                "client_email": client_email,
                "issued_at": issued_at,
                "expires_at": expires_at,
                "is_active": True,
                "signed_certificate": signed_certificate
            })
            
            logger.info(f"Generated certificate for {client_name}")
            return {
                "certificate_id": certificate_id,
                "client_name": client_name,
                "client_email": client_email,
                "certificate": signed_certificate,
                "expires_at": expires_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating certificate: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Error generating client certificate"
            )
    
    async def validate_certificate(self, certificate: str) -> dict:
        """Validate a client certificate"""
        try:
            # Get public key for verification
            public_key_pem = self.public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ).decode()
            
            # Decode and verify certificate
            payload = jwt.decode(
                certificate, 
                public_key_pem, 
                algorithms=[CERTIFICATE_ALGORITHM]
            )
            
            # Check expiration
            expires_at = datetime.fromisoformat(payload['expires_at'])
            if expires_at < datetime.utcnow():
                raise HTTPException(
                    status_code=401, 
                    detail="Certificate has expired"
                )
            
            # Verify certificate exists in database and is active
            cert_record = await db.certificates.find_one({
                "certificate_id": payload['certificate_id'],
                "is_active": True
            })
            
            if not cert_record:
                raise HTTPException(
                    status_code=401, 
                    detail="Certificate not found or has been revoked"
                )
            
            return payload
            
        except JWTError as e:
            logger.warning(f"Invalid certificate: {e}")
            raise HTTPException(
                status_code=401, 
                detail="Invalid certificate"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error validating certificate: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Error validating certificate"
            )

    async def revoke_certificate(self, certificate_id: str):
        """Revoke a client certificate"""
        try:
            result = await db.certificates.update_one(
                {"certificate_id": certificate_id},
                {"$set": {"is_active": False, "revoked_at": datetime.utcnow()}}
            )
            if result.matched_count == 0:
                raise HTTPException(
                    status_code=404, 
                    detail="Certificate not found"
                )
            logger.info(f"Revoked certificate {certificate_id}")
            return {"message": "Certificate revoked successfully"}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error revoking certificate: {e}")
            raise HTTPException(
                status_code=500, 
                detail="Error revoking certificate"
            )

# Global certificate manager instance
cert_manager = CertificateManager()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user from certificate"""
    try:
        if not credentials.credentials:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Certificate required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate certificate
        user_data = await cert_manager.validate_certificate(credentials.credentials)
        return user_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting current user: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )

# Admin authentication (simplified for demo - in production use proper admin auth)
ADMIN_SECRET = os.environ.get('ADMIN_SECRET', 'joinery_admin_2024_secret_key')

async def get_admin_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency for admin-only endpoints"""
    try:
        if credentials.credentials != ADMIN_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin access required",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return {"role": "admin", "client_name": "Admin User"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid admin authentication",
            headers={"WWW-Authenticate": "Bearer"},
        )