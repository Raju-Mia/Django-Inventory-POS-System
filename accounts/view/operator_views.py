from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from rest_framework.permissions import IsAuthenticated


from accounts.models import CustomUser, Organization
from accounts.serializer.operator_serializers import OperatorSerializer


# Filtering Class
class OperatorFilter(filters.FilterSet):
    full_name = filters.CharFilter(lookup_expr="icontains")
    phone = filters.CharFilter(lookup_expr="icontains")
    organization = filters.NumberFilter(field_name="organization__id")
    is_active = filters.BooleanFilter()
    is_verified = filters.BooleanFilter()
    role = filters.CharFilter(lookup_expr="icontains")

    class Meta:
        model = CustomUser
        fields = ["full_name", "phone", "organization", "is_active", "is_verified", "role"]

# List Operators with Filtering
class OperatorListAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        # ✅ Ensure user has organization
        if not user.organization:
            return Response({"error": "You do not belong to any organization."},
                            status=status.HTTP_403_FORBIDDEN)

        # ✅ Filter only operators in this organization
        queryset = CustomUser.objects.filter(
            role="operator",
            organization=user.organization
        )

        # Apply filters
        filterset = OperatorFilter(request.GET, queryset=queryset)
        if not filterset.is_valid():
            return Response(filterset.errors, status=status.HTTP_400_BAD_REQUEST)

        queryset = filterset.qs
        serializer = OperatorSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)




# Create Operator
class OperatorCreateAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        # Operators cannot create new operators
        if request.user.role == "operator":
            return Response(
                {"error": "Operators are not allowed to create new operators."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Must belong to an organization
        if not request.user.organization:
            return Response(
                {"error": "You are not assigned to any organization."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = OperatorSerializer(data=request.data, context={"request": request})
        if serializer.is_valid():
            operator = serializer.save()
            response_data = OperatorSerializer(operator).data
            response_data["password"] = getattr(operator, "generated_password", None)
            return Response(response_data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# Operator Details
class OperatorDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        operator = get_object_or_404(
            CustomUser,
            id=id,
            role="operator",
            organization=request.user.organization
        )
        serializer = OperatorSerializer(operator)
        return Response(serializer.data, status=status.HTTP_200_OK)



# Soft Delete Operator
class OperatorDeleteAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, id):
        # Operators cannot delete others
        if request.user.role == "operator":
            return Response(
                {"error": "Operators are not allowed to delete operators."},
                status=status.HTTP_403_FORBIDDEN
            )

        # Must belong to an organization
        if not request.user.organization:
            return Response(
                {"error": "You are not assigned to any organization."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # ✅ Delete only if operator belongs to same organization
        operator = get_object_or_404(
            CustomUser,
            id=id,
            role="operator",
            organization=request.user.organization
        )

        operator.is_active = False
        operator.is_terminated = True
        operator.save()
        return Response({"detail": "Operator soft deleted successfully."}, status=status.HTTP_200_OK)
