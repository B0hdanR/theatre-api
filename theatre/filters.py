import django_filters

from theatre.models import Play


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
