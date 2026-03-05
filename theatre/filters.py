import django_filters

from theatre.models import Play, Performance


class CommaSeparatedNumberFilter(django_filters.BaseInFilter, django_filters.NumberFilter):
    pass


class PlayFilter(django_filters.FilterSet):
    """
    FilterSet for Play model
    Filter by genres,actors(comma-separated ids) and title
    """

    title = django_filters.CharFilter(
        lookup_expr="icontains",
        field_name="title",
        help_text="Filter plays by title",
    )

    genres = CommaSeparatedNumberFilter(
        lookup_expr="in",
        field_name="genres__id",
        help_text="Filter plays by genres (ex. ?genres=2,3)",
    )

    actors = CommaSeparatedNumberFilter(
        lookup_expr="in",
        field_name="actors__id",
        help_text="Filter plays by actors (ex. ?actors=1,2)",
    )

    class Meta:
        model = Play
        fields = ["title", "genres", "actors"]


class PerformanceFilter(django_filters.FilterSet):
    """
    FilterSet for Performance model
    Filter by play id and dates
    """

    play = django_filters.NumberFilter(
        lookup_expr="exact",
        field_name="play__id",
        help_text="Filter performances by play id",
    )

    date_from = django_filters.DateFilter(
        lookup_expr="gte",
        field_name="show_time__date",
        help_text="Filter performances from this date (YYYY-MM-DD)",
    )

    date_to = django_filters.DateFilter(
        lookup_expr="lte",
        field_name="show_time__date",
        help_text="Filter performances up to this date (YYYY-MM-DD)",
    )

    class Meta:
        model = Performance
        fields = ["play", "date_from", "date_to"]
