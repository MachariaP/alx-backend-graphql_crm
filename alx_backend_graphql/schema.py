import graphene


class CRMQuery(graphene.ObjectType):
    pass


class Query(CRMQuery, graphene.ObjectType):
    hello = graphene.String(default_value="Hello, GraphQL!")


schema = graphene.Schema(query=Query)
