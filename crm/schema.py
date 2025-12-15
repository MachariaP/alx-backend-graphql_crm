import graphene
from graphene_django import DjangoObjectType
from django.db import transaction
from .models import Customer, Product, Order

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone")

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")

class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String()

class ProductInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    price = graphene.Decimal(required=True)
    stock = graphene.Int()

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
                phone=input.phone or None
            )
            return CreateCustomer(customer=customer, message="Customer created successfully")
        except Exception as e:
            return CreateCustomer(customer=None, message=str(e))

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    @transaction.atomic
    def mutate(self, info, input):
        created = []
        errors = []
        for data in input:
            try:
                customer = Customer.objects.create(
                    name=data.name,
                    email=data.email,
                    phone=data.phone or None
                )
                created.append(customer)
            except Exception as e:
                errors.append(f"Error for {data.email}: {str(e)}")
        return BulkCreateCustomers(customers=created, errors=errors or None)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    product = graphene.Field(ProductType)

    def mutate(self, info, input):
        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock or 0
        )
        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids):
        if len(product_ids) == 0:
            raise Exception("At least one product is required")

        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID")

        products = []
        for pid in product_ids:
            try:
                products.append(Product.objects.get(id=pid))
            except Product.DoesNotExist:
                raise Exception(f"Invalid product ID: {pid}")

        order = Order.objects.create(customer=customer)
        order.products.set(products)
        order.save()  # Triggers total_amount calculation

        return CreateOrder(order=order)

class Query(graphene.ObjectType):
    # Add any queries here if needed (task focuses on mutations)
    hello = graphene.String(default_value="Hello from CRM!")

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
