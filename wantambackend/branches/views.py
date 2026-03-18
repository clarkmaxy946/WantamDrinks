# branches/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from .models import Branch
from .serializers import BranchSerializer, AdminBranchSerializer
from .services import get_active_branches


class BranchListView(APIView):
    """
    GET /api/branches/
    Public — no token required.
    Returns only active branches for customer branch selection.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        branches = get_active_branches()
        serializer = BranchSerializer(branches, many=True)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AdminBranchListView(APIView):
    """
    GET  /api/admin/branches/ → list all branches with alert summary
    POST /api/admin/branches/ → create new branch
    Admin only — requires is_staff=True.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        branches = Branch.objects.prefetch_related(
            'alerts',
            'inventory_records'
        ).all()

        serializer = AdminBranchSerializer(branches, many=True)
        data = serializer.data
        return Response(
            {
                "total_branches": len(data),
                "branches": data
            },
            status=status.HTTP_200_OK
        )

    def post(self, request):
        serializer = AdminBranchSerializer(data=request.data)
        if serializer.is_valid():
            branch = serializer.save()
            return Response(
                {
                    "message": f"Branch '{branch.name}' created successfully.",
                    "data": AdminBranchSerializer(branch).data
                },
                status=status.HTTP_201_CREATED
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AdminBranchDetailView(APIView):
    """
    GET    /api/admin/branches/<branch_id>/ → single branch detail
    PATCH  /api/admin/branches/<branch_id>/ → update branch details
    DELETE /api/admin/branches/<branch_id>/ → delete inactive branch
    Admin only — requires is_staff=True.
    """
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_branch(self, branch_id):
        try:
            return Branch.objects.prefetch_related(
                'alerts',
                'inventory_records'
            ).get(branch_id=branch_id)
        except Branch.DoesNotExist:
            return None

    def get(self, request, branch_id):
        branch = self.get_branch(branch_id)
        if not branch:
            return Response(
                {"error": f"Branch '{branch_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminBranchSerializer(branch)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )

    def patch(self, request, branch_id):
        branch = self.get_branch(branch_id)
        if not branch:
            return Response(
                {"error": f"Branch '{branch_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = AdminBranchSerializer(
            branch,
            data=request.data,
            partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "message": f"Branch '{branch_id}' updated successfully.",
                    "data": serializer.data
                },
                status=status.HTTP_200_OK
            )
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )

    def delete(self, request, branch_id):
        branch = self.get_branch(branch_id)
        if not branch:
            return Response(
                {"error": f"Branch '{branch_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Must deactivate before deleting
        if branch.is_active:
            return Response(
                {
                    "error": f"Branch '{branch.name}' is still active. "
                             f"Deactivate it first before deleting."
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        branch_name = branch.name
        branch.delete()
        return Response(
            {"message": f"Branch '{branch_name}' deleted successfully."},
            status=status.HTTP_200_OK
        )

