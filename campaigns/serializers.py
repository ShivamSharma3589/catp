from rest_framework import serializers

from .models import CampaignFlag, CampaignNote, CampaignTarget


class AuthorSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    email = serializers.EmailField()
    full_name = serializers.CharField()
    picture = serializers.CharField()


class CampaignNoteSerializer(serializers.ModelSerializer):
    author = AuthorSerializer(read_only=True)

    class Meta:
        model = CampaignNote
        fields = ('id', 'platform', 'campaign_id', 'author', 'body', 'created_at', 'updated_at')
        read_only_fields = ('id', 'platform', 'campaign_id', 'author', 'created_at', 'updated_at')


class CampaignFlagSerializer(serializers.ModelSerializer):
    raised_by = AuthorSerializer(read_only=True)
    resolved_by = AuthorSerializer(read_only=True)

    class Meta:
        model = CampaignFlag
        fields = (
            'id', 'platform', 'campaign_id', 'reason', 'detail', 'status',
            'raised_by', 'resolved_by', 'created_at', 'resolved_at',
        )
        read_only_fields = (
            'id', 'platform', 'campaign_id', 'raised_by', 'resolved_by',
            'created_at', 'resolved_at',
        )


class CampaignTargetSerializer(serializers.ModelSerializer):
    class Meta:
        model = CampaignTarget
        fields = (
            'id', 'platform', 'campaign_id', 'kpi', 'target_value', 'currency', 'direction',
            'at_risk_threshold_pct', 'off_track_threshold_pct', 'is_primary', 'updated_at',
        )
        read_only_fields = ('id', 'platform', 'campaign_id', 'updated_at')
