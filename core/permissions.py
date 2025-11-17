from rest_framework.permissions import BasePermission, SAFE_METHODS

class RolePermission(BasePermission):
    
    '''
    🔥 Staff
        Can view everything (SAFE methods)
        Can create except User & Organization
        ❌ Cannot update
        ❌ Cannot delete
        ❌ Cannot access ANY reports
        ❌ Cannot access user management
        
    🔥 Operator
        Can view only:
            Products
            Categories
            Suppliers
        ❌ Cannot access reports
        ❌ Cannot access user management

    🔥 Manager
        Can access everything EXCEPT User Management
        ❌ Cannot manage users
        ❌ Cannot create/update/delete users
        Can access reports
        
    🔥 Admin
        Full access to everything
    '''

    def has_permission(self, request, view):
        user = request.user
        print("user Role: ", user)

        if not user or not user.is_authenticated:
            return False

        role = getattr(user, "role", None)
        view_name = view.__class__.__name__

        # All report endpoints end with "ReportAPIView"
        is_report_view = view_name in [
            # "OperatorListAPIView",
            # "OperatorCreateAPIView",
            # "OperatorDetailAPIView",
            # "OperatorDeleteAPIView",
            "SalesReportAPIView",
            "StockReportAPIView",
            "InventoryDashboardAPIView"
        ]

        # ----------------------
        # 🔥 1. ADMIN — Full access
        # ----------------------
        if role == "admin":
            return True

        # ----------------------
        # 🔥 2. MANAGER — Full access EXCEPT user management
        # ----------------------
        if role == "manager":
            if view_name in ["OperatorCreateAPIView", "OperatorListAPIView", "OperatorDetailAPIView", "OperatorDeleteAPIView", "UserViewSet", "OrganizationViewSet"]:
                return False
            return True  # Can access reports too

        # ----------------------
        # 🔥 3. STAFF ROLE
        # ----------------------
        if role == "staff":

            # ❌ Staff CANNOT access reports
            if is_report_view:
                return False

            # ❌ Staff CANNOT access users or organization
            if view_name in ["OperatorCreateAPIView", "OperatorListAPIView", "OperatorDetailAPIView", "OperatorDeleteAPIView", "UserViewSet", "OrganizationViewSet"]:
                return False

            # Staff can READ everything
            if request.method in SAFE_METHODS:
                return True

            # Staff can CREATE except user/organization
            if request.method == "POST":
                return True  # already blocked above

            # No update or delete
            return False

        # ----------------------
        # 🔥 4. OPERATION ROLE
        # ----------------------
        if role == "operation":

            # Allowed viewsets
            allowed_reads = [
                "ProductViewSet",
                "CategoryViewSet",
                "SupplierViewSet"
            ]

            # Only read allowed
            if request.method in SAFE_METHODS:
                return view_name in allowed_reads

            # ❌ No write access
            return False

        # Unknown role = deny
        return False
