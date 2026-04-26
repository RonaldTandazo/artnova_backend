import strawberry

@strawberry.input
class SearchInput:
    search: str
    pageArtworks: int
    pageArtists: int
    type: str