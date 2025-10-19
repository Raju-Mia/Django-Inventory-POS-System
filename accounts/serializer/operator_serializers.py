import random
import string
from rest_framework import serializers
from accounts.models import CustomUser, Organization



def generate_random_password(length=10):
    """Generate a random secure password."""
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choices(characters, k=length))


class OrganizationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ["id", "name", "address", "created_by", "created_at"]


class OperatorSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "full_name",
            "phone_number",
            "role",
            "organization",
            "address",
            "profile_picture",
            "is_verified",
            "is_active",
            "is_block",
            "is_terminated",
            "created_at",
            "password",
        ]
        read_only_fields = ["id", "organization", "role", "created_at"]

    def create(self, validated_data):
        request = self.context.get("request")
        creator = request.user if request else None

        password = validated_data.pop("password", None)
        if not password:
            password = generate_random_password()

        # Always assign operator role
        validated_data["role"] = "operator"

        # 🔑 Generate a unique username
        base_username = (validated_data.get("full_name") or "operator").replace(" ", "").lower()
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"{base_username}{random_suffix}"
        while CustomUser.objects.filter(username=username).exists():
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            username = f"{base_username}{random_suffix}"

        # Build user
        user = CustomUser(
            username=username,   # 👈 important
            **validated_data
        )
        user.set_password(password)

        # ✅ If creator has an organization, assign it
        if creator and creator.organization:
            user.organization = creator.organization

        user.save()

        # ✅ If still no organization, auto-create
        if not user.organization:
            org = Organization.objects.create(
                name=f"Org-{user.full_name or user.id}",
                created_by=user,
            )
            user.organization = org
            user.save(update_fields=["organization"])
            
            
        # Attach generated password so we can return it in response
        user.generated_password = password
        return user
