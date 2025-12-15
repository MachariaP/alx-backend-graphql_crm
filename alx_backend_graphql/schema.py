import graphene
from crm.schema import Query as CRMQuery, Mutation as CRMMutation

class CRMQueryBase(graphene.ObjectType):
    pass

class Query(CRMQueryBase, CRMQuery, graphene.ObjectType):
    pass

class Mutation(CRMMutation, graphene.ObjectType):
    pass

schema = graphene.Schema(query=Query, mutation=Mutation)
