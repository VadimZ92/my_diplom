from django.urls import path
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
