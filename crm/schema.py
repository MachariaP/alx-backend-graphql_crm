import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction
from django.core.exceptions import ValidationError
import re
from .models import Customer, Product, Order, OrderItem


# ==================== TYPES ====================
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        interfaces = (graphene.relay.Node,)
        fields = "__all__"


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        interfaces = (graphene.relay.Node,)
        fields = "__all__"


class OrderItemType(DjangoObjectType):
    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderType(DjangoObjectType):
    customer = graphene.Field(CustomerType)
    products = graphene.List(ProductType)
    order_items = graphene.List(OrderItemType)
    
    class Meta:
        model = Order
        interfaces = (graphene.relay.Node,)
        fields = "__all__"
    
    def resolve_customer(self, info):
        return self.customer
    
    def resolve_products(self, info):
        return self.products.all()
    
    def resolve_order_items(self, info):
        return self.orderitem_set.all()


# ==================== QUERIES ====================
class Query(graphene.ObjectType):
    # Task 0: Hello query
    hello = graphene.String(default_value="Hello, GraphQL!")
    
    # Customer queries
    customer = graphene.Field(CustomerType, id=graphene.UUID(required=True))
    all_customers = DjangoFilterConnectionField(CustomerType)
    
    # Product queries
    product = graphene.Field(ProductType, id=graphene.UUID(required=True))
    all_products = DjangoFilterConnectionField(ProductType)
    
    # Order queries
    order = graphene.Field(OrderType, id=graphene.UUID(required=True))
    all_orders = DjangoFilterConnectionField(OrderType)
    
    def resolve_customer(self, info, id):
        return Customer.objects.get(id=id)
    
    def resolve_all_customers(self, info, **kwargs):
        return Customer.objects.all()
    
    def resolve_product(self, info, id):
        return Product.objects.get(id=id)
    
    def resolve_all_products(self, info, **kwargs):
        return Product.objects.all()
    
    def resolve_order(self, info, id):
        return Order.objects.get(id=id)
    
    def resolve_all_orders(self, info, **kwargs):
        return Order.objects.all()
