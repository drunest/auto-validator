import json
import time

from bittensor import Keypair
from django.conf import settings
from rest_framework import authentication, exceptions

from .models import Hotkey


class HotkeyAuthentication(authentication.BaseAuthentication):
    def authenticate(self, request):
        hotkey_address = request.headers.get("Hotkey")
        nonce = request.headers.get("Nonce")
        signature = request.headers.get("Signature")
        method = request.method.upper()
        url = request.build_absolute_uri()

        if method == "GET":
            return (None, None)

        if not hotkey_address or not nonce or not signature:
            raise exceptions.AuthenticationFailed("Missing authentication headers.")

        nonce_float = float(nonce)
        current_time = time.time()
        if abs(current_time - nonce_float) > int(settings.SIGNATURE_EXPIRE_DURATION):
            raise exceptions.AuthenticationFailed("Invalid nonce")

        if not Hotkey.objects.filter(hotkey=hotkey_address).exists():
            raise exceptions.AuthenticationFailed("Unauthorized hotkey.")

        client_headers = {
            "Nonce": nonce,
            "Hotkey": hotkey_address,
            "Note": request.headers.get("Note"),
            "SubnetID": request.headers.get("SubnetID"),
            "Realm": request.headers.get("Realm"),
        }
        client_headers = {k: v for k, v in client_headers.items() if v is not None}
        headers_str = json.dumps(client_headers, sort_keys=True)

        data_to_sign = f"{method}{url}{headers_str}"

        if "file" in request.FILES:
            uploaded_file = request.FILES["file"]
            file_content = uploaded_file.read()
            decoded_file_content = file_content.decode(errors="ignore")
            data_to_sign += decoded_file_content

        data_to_sign = data_to_sign.encode()
        try:
            is_valid = Keypair(ss58_address=hotkey_address).verify(
                data=data_to_sign, signature=bytes.fromhex(signature)
            )
        except Exception as e:
            raise exceptions.AuthenticationFailed(f"Signature verification failed: {e}")

        if not is_valid:
            raise exceptions.AuthenticationFailed("Invalid signature.")

        return (None, None)
