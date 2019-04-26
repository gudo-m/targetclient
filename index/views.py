from django.shortcuts import render


def main(request):
    args = {'index': True}  # данные
    if request.user.is_staff:  # если админ, говорим
        args['admin'] = True

    return render(request, 'index/index.html', args)


def using_request(request):
    args = {'index': True}  # данные
    if request.user.is_staff:  # если админ, говорим
        args['admin'] = True

    return render(request, 'index/using_request.html', args)
