import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction, IntegrityError
from django.db.models import F
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
        order.save()

        return CreateOrder(order=order)


# NEW MUTATION: UpdateLowStockProducts
class UpdateLowStockProducts(graphene.Mutation):
    """
    Mutation to update low-stock products (stock < 10)
    Increments their stock by 10 (simulating restocking)
    """
    class Arguments:
        increment_by = graphene.Int(default_value=10, description="Amount to increment stock by")
    
    success = graphene.Boolean()
    message = graphene.String()
    update_count = graphene.Int()
    updated_products = graphene.List(ProductType)
    
    def mutate(self, info, increment_by=10):
        try:
            # Query products with stock < 10
            low_stock_products = Product.objects.filter(stock__lt=10)
            
            if not low_stock_products.exists():
                return UpdateLowStockProducts(
                    success=True,
                    message="No low-stock products found (stock < 10)",
                    update_count=0,
                    updated_products=[]
                )
            
            # Store product IDs before update for returning
            product_ids = list(low_stock_products.values_list('id', flat=True))
            
            # Increment stock by specified amount
            updated_count = low_stock_products.update(stock=F('stock') + increment_by)
            
            # Get the updated products
            updated_products = Product.objects.filter(id__in=product_ids)
            
            return UpdateLowStockProducts(
                success=True,
                message=f"Successfully updated {updated_count} low-stock products",
                update_count=updated_count,
                updated_products=updated_products
            )
            
        except Exception as e:
            return UpdateLowStockProducts(
                success=False,
                message=f"Error updating low-stock products: {str(e)}",
                update_count=0,
                updated_products=[]
            )


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


# Mutation root - ADD THE NEW MUTATION HERE
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()
