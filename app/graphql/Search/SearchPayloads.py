import strawberry
from app.graphql.Artwork.ArtworkPayloads import ArtworkPayload
from app.graphql.User.UserPayloads import ArtistPayload

@strawberry.type
class SearchPayload:
    artworks: list[ArtworkPayload]
    hasMoreArtworks: bool
    artists: list[ArtistPayload]
    hasMoreArtists: bool
    type: str