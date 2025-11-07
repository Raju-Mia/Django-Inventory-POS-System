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
        fields = ["id", "name", "email", "phone", "address", "is_active", "created_at"]


class OperatorSerializer(serializers.ModelSerializer):
    organization = OrganizationSerializer(read_only=True)
    password = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "first_name",
            "last_name",
            "email",
            "phone",
            "role",
            "organization",
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

        # Generate random password if not provided
        password = validated_data.pop("password", None) or generate_random_password()

        # Always assign role = operator
        # validated_data["role"] = 

        # ✅ Generate unique username
        base_username = (validated_data.get("first_name") or "operator").replace(" ", "").lower()
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
        username = f"{base_username}{random_suffix}"
        while CustomUser.objects.filter(username=username).exists():
            random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
            username = f"{base_username}{random_suffix}"

        # Create operator user
        user = CustomUser(
            username=username,
            **validated_data,
            

        )
        user.set_password(password)

        # ✅ Assign organization from creator if available
        if creator and creator.organization:
            user.organization = creator.organization

        user.is_active = True
        user.is_verified = True
        user.save()

        # ✅ If user still has no organization, auto-create one
        if not user.organization:
            org = Organization.objects.create(
                name=f"Org-{user.first_name or user.email}",
            )
            user.organization = org
            user.save(update_fields=["organization"])

        # Attach generated password (for returning to API)
        user.generated_password = password
        return user
