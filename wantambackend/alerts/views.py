# alerts/views.py
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.core.exceptions import ValidationError
from .models import StockAlert
from .serializers import (
    StockAlertSerializer,
    ResolveAlertSerializer,
    AlertSummarySerializer,
)


class AdminAlertListView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        alerts = StockAlert.objects.select_related(
            'inventory',
            'branch',
            'product',
            'resolved_by'
        ).order_by('-created_at')

        # Filter by is_resolved
        is_resolved = request.query_params.get('is_resolved')
        if is_resolved is not None:
            if is_resolved.lower() == 'false':
                alerts = alerts.filter(is_resolved=False)
            elif is_resolved.lower() == 'true':
                alerts = alerts.filter(is_resolved=True)

        # Filter by branch
        branch_id = request.query_params.get('branch_id')
        if branch_id:
            alerts = alerts.filter(branch__branch_id=branch_id)

        # Filter by product
        product_id = request.query_params.get('product_id')
        if product_id:
            alerts = alerts.filter(product__product_id=product_id)

        # Filter by severity
        severity = request.query_params.get('severity')
        if severity:
            alerts = alerts.filter(severity=severity.upper())

        # COUNT(*) in SQL — runs before serialization, no rows pulled into memory
        total_alerts = alerts.count()
        serializer = StockAlertSerializer(alerts, many=True)
        return Response(
            {
                "total_alerts": total_alerts,
                "alerts": serializer.data
            },
            status=status.HTTP_200_OK
        )


class AdminAlertDetailView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get_alert(self, alert_id):
        try:
            return StockAlert.objects.select_related(
                'inventory',
                'branch',
                'product',
                'resolved_by'
            ).get(id=alert_id)
        except StockAlert.DoesNotExist:
            return None

    def get(self, request, alert_id):
        alert = self.get_alert(alert_id)
        if not alert:
            return Response(
                {"error": f"Alert '{alert_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )
        serializer = StockAlertSerializer(alert)
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )


class AdminAlertResolveView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def post(self, request, alert_id):
        try:
            alert = StockAlert.objects.select_related(
                'inventory',
                'branch',
                'product'
            ).get(id=alert_id)
        except StockAlert.DoesNotExist:
            return Response(
                {"error": f"Alert '{alert_id}' not found."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = ResolveAlertSerializer(
            data={},
            context={
                'request': request,
                'alert': alert
            }
        )

        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            resolved_alert = serializer.save()
        except ValidationError as e:
            error_detail = e.message_dict if hasattr(e, 'message_dict') else {"error": e.message}
            return Response(
                {
                    "action_required": "restock",
                    **error_detail
                },
                status=status.HTTP_400_BAD_REQUEST
            )

        return Response(
            {
                "message": f"Alert for {alert.product.name} at "
                           f"{alert.branch.name} resolved successfully.",
                "resolved_by": str(request.user),
                "resolved_at": resolved_alert.resolved_at,
            },
            status=status.HTTP_200_OK
        )


class AdminAlertSummaryView(APIView):
    
    permission_classes = [IsAuthenticated, IsAdminUser]

    def get(self, request):
        unresolved = StockAlert.objects.filter(is_resolved=False)

        total_unresolved = unresolved.count()
        critical_count = unresolved.filter(
            severity=StockAlert.Severity.CRITICAL
        ).count()
        low_count = unresolved.filter(
            severity=StockAlert.Severity.LOW
        ).count()

        # Unique branch names with unresolved alerts
        branches_affected = list(
            unresolved.values_list(
                'branch__name', flat=True
            ).distinct()
        )

        serializer = AlertSummarySerializer({
            "total_unresolved": total_unresolved,
            "critical_count": critical_count,
            "low_count": low_count,
            "branches_affected": branches_affected,
        })

        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )