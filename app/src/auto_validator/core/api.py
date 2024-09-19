from rest_framework import mixins, parsers, routers, viewsets
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from auto_validator.core.models import Hotkey, Server, UploadedFile, ValidatorInstance
from auto_validator.core.serializers import UploadedFileSerializer
from auto_validator.core.utils.decorators import get_user_ip, verify_signature_and_route_subnet


class FilesViewSet(mixins.CreateModelMixin, mixins.ListModelMixin, viewsets.GenericViewSet):
    serializer_class = UploadedFileSerializer
    parser_classes = [parsers.MultiPartParser]
    authentication_classes = []
    permission_classes = []

    def get_queryset(self):
        hotkey_str = self.request.headers.get("Hotkey")
        try:
            hotkey = Hotkey.objects.get(hotkey=hotkey_str)
        except Hotkey.DoesNotExist:
            return []
        return UploadedFile.objects.filter(hotkey=hotkey).order_by("id")

    @verify_signature_and_route_subnet
    def create(self, request, *args, **kwargs) -> Response:
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        note = self.request.headers.get("Note")
        hotkey_str = self.request.headers.get("Hotkey")
        ip_address = get_user_ip(self.request)
        try:
            hotkey = Hotkey.objects.get(hotkey=hotkey_str)
            server = Server.objects.get(ip_address=ip_address)
            subnetslot = ValidatorInstance.objects.get(hotkey=hotkey, server=server).subnet_slot
        except ValidatorInstance.DoesNotExist:
            raise ValidationError("Invalid Hotkey")
        serializer.save(
            meta_info={
                "note": note,
                "hotkey": hotkey_str,
                "subnet_name": subnetslot.subnet.name,
                "netuid": subnetslot.netuid,
            }
        )


class APIRootView(routers.DefaultRouter.APIRootView):
    description = "api-root"


class APIRouter(routers.DefaultRouter):
    APIRootView = APIRootView


router = APIRouter()
router.register(r"files", FilesViewSet, basename="file")
