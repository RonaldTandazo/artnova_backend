import strawberry

@strawberry.input
class PaginationInput:
    limit: int = 10
    offset: int = 0