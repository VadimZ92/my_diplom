from django.urls import path
# from rest_framework.routers import DefaultRouter
from backend.views import ContractorUpdate, ShopView, CategoryView, ProductInfoView, RegisterUser, LoginUser,\
    BasketView, ContactView, OrderView, ContractorOrders, ContractorState, PasswordReset

app_name = 'backend'
urlpatterns = [
    path('contractor/update', ContractorUpdate.as_view(), name='contractor-update'),
    path('contractor/state', ContractorState.as_view(), name='contractor-state'),
    path('contractor/orders', ContractorOrders.as_view(), name='contractor-orders'),
    path('user/register', RegisterUser.as_view(), name='user-register'),
    path('user/contact', ContactView.as_view(), name='user-contact'),
    path('user/login', LoginUser.as_view(), name='user-login'),
    path('user/password_reset', PasswordReset.as_view(), name='password-reset'),
    path('categories', CategoryView.as_view(), name='categories'),
    path('shops', ShopView.as_view(), name='shops'),
    path('products', ProductInfoView.as_view(), name='shops'),
    path('basket', BasketView.as_view(), name='basket'),
    path('order', OrderView.as_view(), name='order'),

]
#
# router = DefaultRouter()
# router.register('contractor/update', ContractorUpdate)
# router.register('contractor/state', ContractorState)
# router.register('contractor/orders', ContractorOrders)
# router.register('user/register', RegisterUser)
# router.register('user/contact', ContactView)
# router.register('user/login', LoginUser)
# router.register('user/password_reset', PasswordReset)
# router.register('categories', CategoryView)
# router.register('shops', ShopView)
# router.register('products', ProductInfoView)
# router.register('basket', BasketView)
# router.register('order', OrderView)
# urlpatterns = router.urls
