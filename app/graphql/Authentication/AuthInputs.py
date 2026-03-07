import strawberry

@strawberry.input
class ValidateAccessInput:
    value: int
    module: str
