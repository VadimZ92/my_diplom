from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from distutils.util import strtobool
from backend.models import Shop, Category, Product, ProductParameter, ProductInfo, Parameter, User,\
    Order, OrderItem, Contact
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q, Sum, F
from django.http import JsonResponse
from requests import get
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from ujson import loads as load_json
from yaml import load as load_yaml, Loader
import os
from backend.serializers import ShopSerializer, CategorySerializer, ProductInfoSerializer, UserSerializer,\
    OrderItemSerializer, OrderSerializer, OrderItemCreateSerializer, ContactSerializer
from backend.models import User
import yaml


class RegisterUser(APIView):
    """
    Для регистрации покупателей
    """
    # Регистрация методом POST
    def post(self, request, *args, **kwargs):

        # проверяем обязательные аргументы
        if {'first_name', 'last_name', 'email', 'password'}.issubset(request.data):
            errors = {}

            # проверяем пароль на сложность
            try:
                validate_password(request.data['password'])
            except Exception as password_error:
                error_array = []
                # noinspection PyTypeChecker
                for item in password_error:
                    error_array.append(item)
                return JsonResponse({'Status': False, 'Errors': {'password': error_array}})

            else:
                # проверяем данные для уникальности имени пользователя
                request.data._mutable = True
                request.data.update({})
                user_serializer = UserSerializer(data=request.data)
                if user_serializer.is_valid():
                    # сохраняем пользователя
                    user = user_serializer.save()
                    user.save()
                    return JsonResponse({'Status': True})

                else:
                    return JsonResponse({'Status': False, 'Errors': user_serializer.errors})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class LoginUser(APIView):
    """
    Класс для авторизации пользователей
    """
    # Авторизация методом POST
    def post(self, request, *args, **kwargs):

        if {'email', 'password'}.issubset(request.data):
            email = request.POST.get('email')
            password = request.POST.get('password')
            u = User.objects.get(email=email)
            u.set_password(password)
            u.is_active = True
            u.save()
            user = authenticate(request, username=email, password=password)
            if user is not None:
                if user.is_active:
                    token, _ = Token.objects.get_or_create(user=user)
                    msg = EmailMultiAlternatives(
                        # title:
                        f"Ваша регистрация подтверждена ",
                        # message:
                        f" Ваш токен:{token.key}",
                        # from:
                        settings.EMAIL_HOST_USER,
                        # to:
                        [user.email]
                    )
                    msg.send()
                    return JsonResponse({'Status': True, 'Token': token.key, "Информация": f"Отправлено "
                                                                                           f"на: '{user.email}'"})
            return JsonResponse({'Status': False, 'Errors': 'Не удалось авторизовать'})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class PasswordReset(APIView):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'password'}.issubset(request.data):
            try:
                is_updated = User.objects.filter(
                    id=request.user.id).update(
                    password=request.data['password'])
            except IntegrityError as error:
                print(error)
                return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})

            else:
                if is_updated:
                    u = User.objects.get(id=request.user.id)
                    # new_order.send(sender=self.__class__, user_id=request.user.id)
                    msg = EmailMultiAlternatives(
                        # title:
                        f"Изменение профиля",
                        # message:
                        f" Ваш пароль изменен",
                        # from:
                        settings.EMAIL_HOST_USER,
                        # to:
                        [u.email]
                    )
                    msg.send()
                    return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ShopView(ListAPIView):
    """
    Класс для просмотра списка магазинов
    """
    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopSerializer


class CategoryView(ListAPIView):
    """
    Класс для просмотра категорий
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ProductInfoView(APIView):
    """
    Класс для поиска товаров
    """
    def get(self, request, *args, **kwargs):

        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')

        if shop_id:
            query = query & Q(shop_id=shop_id)

        if category_id:
            query = query & Q(product__category_id=category_id)

        # фильтруем и отбрасываем дубликаты
        queryset = ProductInfo.objects.filter(
            query).select_related(
            'shop', 'product__category').prefetch_related(
            'product_parameters__parameter').distinct()

        serializer = ProductInfoSerializer(queryset, many=True)

        return Response(serializer.data)


class ContactView(APIView):
    """
    Класс для работы с контактами покупателей
    """

    # получить мои контакты
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        contact = Contact.objects.filter(
            user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    # добавить новый контакт
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'type', 'value'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
            serializer = ContactSerializer(data=request.data)

            if serializer.is_valid():
                serializer.save()
                return JsonResponse({'Status': True})
            else:
                JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # удалить контакт
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    query = query | Q(user_id=request.user.id, id=contact_id)
                    objects_deleted = True
            if objects_deleted:
                deleted_count = Contact.objects.filter(query).delete()[0]
                return JsonResponse({'Status': True, 'Удалено объектов': deleted_count})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # редактировать контакт
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                if contact:
                    serializer = ContactSerializer(contact, data=request.data, partial=True)
                    if serializer.is_valid():
                        serializer.save()
                        return JsonResponse({'Status': True})
                    else:
                        JsonResponse({'Status': False, 'Errors': serializer.errors})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class BasketView(APIView):
    """
    Класс для работы с корзиной пользователя
    """
    # получить корзину
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        basket = Order.objects.filter(
                user_id=request.user.id, state='basket').prefetch_related(
                'ordered_items__shop',
                'ordered_items__product').annotate(
                total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product__price'))).distinct()
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                return JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})

            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_created = 0
                for order_item in items_dict:
                    order_item.update({'order': basket.id})
                    serializer = OrderItemSerializer(data=order_item)
                    if serializer.is_valid():
                        try:
                            serializer.save()
                        except IntegrityError as error:
                            return JsonResponse({'Status': False, 'Errors': str(error)})

                        else:
                            objects_created += 1
                    else:
                        return JsonResponse({'Status': False, 'Errors': serializer.errors})

                return JsonResponse({'Status': True, 'Создано объектов': objects_created})
        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # удалить товары из корзины
    def delete(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        print(items_sting)
        if items_sting:
            items_list = items_sting.split(',')
            print(items_list)
            basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
            count = 0
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    OrderItem.objects.filter(id=order_item_id).delete()
                    count += 1
            return JsonResponse({'Status': True, 'Удалено объектов': count})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})

    # изменить позиции в корзине
    def put(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        items_sting = request.data.get('items')
        if items_sting:
            try:
                items_dict = load_json(items_sting)
            except ValueError:
                JsonResponse({'Status': False, 'Errors': 'Неверный формат запроса'})
            else:
                basket, _ = Order.objects.get_or_create(user_id=request.user.id, state='basket')
                objects_updated = 0
                for order_item in items_dict:
                    if type(order_item['id']) == int and type(order_item['quantity']) == int:
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])
                return JsonResponse({'Status': True, 'Обновлено объектов': objects_updated})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class OrderView(APIView):
    # получить мои заказы
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
        basket = Order.objects.filter(
            user_id=request.user.id, state='new').prefetch_related(
            'ordered_items__shop',
            'ordered_items__product').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product__price'))).distinct()
        serializer = OrderSerializer(basket, many=True)
        return Response(serializer.data)

    # разместить заказ из корзины
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                try:
                    is_updated = Order.objects.filter(
                        user_id=request.user.id, id=request.data['id']).update(
                        contact_id=request.data['contact'],
                        state='new')
                except IntegrityError as error:
                    print(error)
                    return JsonResponse({'Status': False, 'Errors': 'Неправильно указаны аргументы'})

                else:
                    if is_updated:
                        u = User.objects.get(id=request.user.id)
                        msg = EmailMultiAlternatives(
                            # title:
                            f"Статус заказа",
                            # message:
                            f" Ваш заказ сформирован ",
                            # from:
                            settings.EMAIL_HOST_USER,
                            # to:
                            [u.email]
                        )
                        msg.send()
                        return JsonResponse({'Status': True})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})


class ContractorUpdate(APIView):
    """
    Класс для обновления прайса от поставщика
    """
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        catalog = "data"
        file_name = f"{request.data.get('items')}.yaml"
        base_path = os.getcwd()
        full_path = os.path.join(base_path, catalog, file_name)
        with open(full_path, 'r', encoding="utf-8") as fd:
            data = yaml.load(fd, Loader=Loader)
        shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
        for category in data['categories']:
            category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
            category_object.shops.add(shop.id)
            category_object.save()
        ProductInfo.objects.filter(shop_id=shop.id).delete()
        for item in data['goods']:
            product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

            product_info = ProductInfo.objects.create(product_id=product.id,
                                                      external_id=item['id'],
                                                      model=item['model'],
                                                      price=item['price'],
                                                      price_rrc=item['price_rrc'],
                                                      quantity=item['quantity'],
                                                      shop_id=shop.id)
            for name, value in item['parameters'].items():
                parameter_object, _ = Parameter.objects.get_or_create(name=name)
                ProductParameter.objects.create(product_info_id=product_info.id,
                                                parameter_id=parameter_object.id,
                                                value=value)
        return JsonResponse({'Status': True})


class ContractorOrders(APIView):
    """
    Класс для получения заказов поставщиками
    """
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        # order = Order.objects.filter(
        #     ordered_items__shop__user_id=request.user.id).exclude(state='basked').prefetch_related(
        #     'ordered_items__shop',
        #     'ordered_items__product').annotate(
        #     total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product__price'))).distinct()
        order = Order.objects.filter(
            ordered_items__shop_id=request.user.id).exclude(state='basket').select_related('contact').annotate(
            total_sum=Sum(F('ordered_items__quantity') * F('ordered_items__product__price'))).distinct()
        serializer = OrderSerializer(order, many=True)
        u = User.objects.get(id=request.user.id)
        msg = EmailMultiAlternatives(
            # title:
            f"Заказы",
            # message:
            f"Сформирован заказ: {Response(serializer.data).data},"
            f"ваш заказ соответствует магазину: shop{request.user.id}, "
            f"сумма заказа - поле 'total_sum'",
            # from:
            settings.EMAIL_HOST_USER,
            # to:
            [u.email]
        )
        msg.send()
        return Response(serializer.data)


class ContractorState(APIView):
    """
    Класс для работы со статусом поставщика
    """

    # получить текущий статус
    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)

        shop = request.user.shop
        serializer = ShopSerializer(shop)
        return Response(serializer.data)

    # изменить текущий статус
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)

        if request.user.type != 'shop':
            return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
        state = request.data.get('state')
        if state:
            try:
                Shop.objects.filter(user_id=request.user.id).update(state=strtobool(state))
                return JsonResponse({'Status': True})

            except ValueError as error:
                return JsonResponse({'Status': False, 'Errors': str(error)})

        return JsonResponse({'Status': False, 'Errors': 'Не указаны все необходимые аргументы'})
