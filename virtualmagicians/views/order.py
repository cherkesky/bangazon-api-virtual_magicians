"""View module for handling requests about products"""
import json
from django.http import HttpResponseServerError
from rest_framework.decorators import action
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import serializers
from rest_framework import status
from virtualmagicians.models import Order, Product, Customer, OrderProduct
from .product import ProductSerializer

class OrderSerializer(serializers.HyperlinkedModelSerializer):
    """JSON serializer for orders

    Arguments:
        serializers.HyperlinkedModelSerializer
    """
    class Meta:
        model = Order
        url = serializers.HyperlinkedIdentityField(
            view_name='order',
            lookup_field='id'
        )
        fields = ('id', 'url', 'customer', 'payment_type',)
        depth = 2


class Orders(ViewSet):

    """Orders for Bangazon"""

    def retrieve(self, request, pk=None):
        """Handle get request for 1 order
        Returns:
            Response -- JSON serialized order instance
        """

        try:
            order = Order.objects.get(pk=pk)
            serializer = OrderSerializer(order, context={'request': request})
            return Response(serializer.data)
        except Exception as ex:
            return HttpResponseServerError(ex)

    def create(self, request):
        """Handle POST operations
        Returns:
        Response -- JSON serialized Products instance
        """
        current_user = Customer.objects.get(user=request.auth.user)

        try:
            open_order = Order.objects.get(customer=current_user, payment_type=None)

        except Order.DoesNotExist:
            open_order = Order()
            open_order.customer_id = request.auth.user.customer.id
            open_order.save()

        new_orderproduct = OrderProduct()
        new_orderproduct.order_id = open_order.id
        new_orderproduct.product_id = request.data['product_id']
        new_orderproduct.save()

        serializer = OrderSerializer(new_orderproduct, context={'request': request})

        return Response(serializer.data)

    def update(self, request, pk=None):
        """Handle PUT requests for an order

        Returns:
            Response -- Empty body with 204 status code
        """
        customer = request.auth.user.customer
        order = Order.objects.get(pk=pk)
        order.customer_id = customer.id
        order.payment_type_id = request.data["payment_type_id"]
        order.save()

        return Response({}, status=status.HTTP_204_NO_CONTENT)

    def list(self, request):
        """Handle GET requests to get the open order for the logged in user/customer
        Returns:
            Response -- JSON serialized list of users
        """      
        orders = Order.objects.filter(customer_id=request.auth.user.customer.id, payment_type_id=None)
        
        order = self.request.query_params.get('order', None)
        
        if order is not None:
            orders = Order.filter(pk=request.auth.user)

        serializer = OrderSerializer(orders, many=True, context={'request': request})

        return Response(serializer.data)
    
        ################# SHOPPING CART ###############################
    # Example request:
    #   http://localhost:8000/orders/cart
    @action(methods=['get'], detail=False)
    def cart(self, request):
        current_user = Customer.objects.get(user=request.auth.user)
        # try:
        open_order = Order.objects.get(customer=current_user, payment_type=None)
        products_on_order = Product.objects.filter(cart__order=open_order)
        # except Order.DoesNotExist as ex:
        #     return Response({'message': ex.args[0]}, status=status.HTTP_404_NOT_FOUND)
        serializer = ProductSerializer(products_on_order, many=True, context={'request': request})
        return Response(serializer.data)
