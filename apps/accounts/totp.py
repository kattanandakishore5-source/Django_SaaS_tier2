import io
import base64
import pyotp
import qrcode


def generate_totp_secret():
    """Generate a random 32-character base32 TOTP secret."""
    return pyotp.random_base32()


def get_totp_uri(user_email, secret, issuer_name="Django Starter"):
    """Get provisioning URI for authenticator apps."""
    totp = pyotp.TOTP(secret)
    return totp.provisioning_uri(name=user_email, issuer_name=issuer_name)


def generate_qr_code_base64(provisioning_uri):
    """Generate a base64 encoded PNG QR code image for provisioning URI."""
    img = qrcode.make(provisioning_uri)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return base64.b64encode(buf.getvalue()).decode('utf-8')


def verify_totp_code(secret, code):
    """
    Verify a 6-digit TOTP code against the secret.
    Allows 1 step (30 seconds) clock skew window.
    """
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
