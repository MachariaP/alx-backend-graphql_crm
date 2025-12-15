import graphene


class Query(graphene.ObjectType):
    """Root GraphQL query."""
    hello = graphene.String(default_value="Hello, GraphQL!")


# Create the schema
schema = graphene.Schema(query=Query)
