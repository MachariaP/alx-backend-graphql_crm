import graphene
from graphene_django import DjangoObjectType
from django.db import transaction, IntegrityError
from .models import Customer, Product, Order


# DjangoObjectTypes
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


# Input Types
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


# Mutations
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
        order.save()  # This triggers total_amount calculation

        return CreateOrder(order=order)


# CRM Query and Mutation roots
class Query(graphene.ObjectType):
    # Keep the hello field from Task 0 if needed, or leave minimal
    pass


class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
