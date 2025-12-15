import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction, IntegrityError
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter


# DjangoObjectTypes
class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")
        filterset_class = CustomerFilter
        interfaces = (graphene.relay.Node,)


class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        filterset_class = ProductFilter
        interfaces = (graphene.relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")
        filterset_class = OrderFilter
        interfaces = (graphene.relay.Node,)


# Input Types for Mutations
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)


class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int(required=False, default_value=0)


class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(name="customerId", required=True)
    product_ids = graphene.List(graphene.ID, name="productIds", required=True)


# Filter Input Types (for custom argument names in GraphQL)
class CustomerFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String(name="nameIcontains")
    email_icontains = graphene.String(name="emailIcontains")
    created_at_gte = graphene.Date(name="createdAtGte")
    created_at_lte = graphene.Date(name="createdAtLte")
    phone_pattern = graphene.String()


class ProductFilterInput(graphene.InputObjectType):
    name_icontains = graphene.String(name="nameIcontains")
    price_gte = graphene.Float(name="priceGte")
    price_lte = graphene.Float(name="priceLte")
    stock_gte = graphene.Int(name="stockGte")
    stock_lte = graphene.Int(name="stockLte")


class OrderFilterInput(graphene.InputObjectType):
    total_amount_gte = graphene.Float(name="totalAmountGte")
    total_amount_lte = graphene.Float(name="totalAmountLte")
    order_date_gte = graphene.Date(name="orderDateGte")
    order_date_lte = graphene.Date(name="orderDateLte")
    customer_name = graphene.String(name="customerName")
    product_name = graphene.String(name="productName")


# Mutations (unchanged from your working version)
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, input):
        try:
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=getattr(input, "phone", None)
            )
            return CreateCustomer(customer=customer, message="Customer created successfully")
        except IntegrityError:
            return CreateCustomer(customer=None, message="Email already exists")
        except Exception as e:
            return CreateCustomer(customer=None, message=str(e))


class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        created_customers = []
        errors = []

        for item in input:
            try:
                customer = Customer.objects.create(
                    name=item.name,
                    email=item.email,
                    phone=getattr(item, "phone", None)
                )
                created_customers.append(customer)
            except IntegrityError:
                errors.append(f"Email already exists: {item.email}")
            except Exception as e:
                errors.append(f"Invalid data for {item.email}: {str(e)}")

        return BulkCreateCustomers(customers=created_customers, errors=errors or None)


class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock
        )
        return CreateProduct(product=product)


class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, input):
        if not input.product_ids:
            raise Exception("At least one product must be provided")

        try:
            customer = Customer.objects.get(id=input.customer_id)
        except Customer.DoesNotExist:
            raise Exception("Customer with provided ID does not exist")

        products = []
        for pid in input.product_ids:
            try:
                products.append(Product.objects.get(id=pid))
            except Product.DoesNotExist:
                raise Exception(f"Product with ID {pid} does not exist")

        order = Order.objects.create(customer=customer)
        order.products.set(products)
        order.save()

        return CreateOrder(order=order)


# Query with Filtering and Ordering
class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filter=CustomerFilterInput(),
        order_by=graphene.List(of_=graphene.String)
    )
    all_products = DjangoFilterConnectionField(
        ProductType,
        filter=ProductFilterInput(),
        order_by=graphene.List(of_=graphene.String)
    )
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filter=OrderFilterInput(),
        order_by=graphene.List(of_=graphene.String)
    )

    hello = graphene.String(default_value="Hello, GraphQL!")


# Mutation root
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
