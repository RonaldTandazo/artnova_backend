import strawberry

@strawberry.input
class ValidateAccessInput:
    value: int | None
    module: str
