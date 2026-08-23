from rest_framework import serializers


class DashboardStatsSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    users_by_role = serializers.DictField()
    registrations_30d = serializers.IntegerField()
