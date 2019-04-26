$('#check_root').click(function () {
    $(".errors").append('<div class="alert alert-info" id="error_output" role="alert">Список обновится через некоторое время, мы сообщим вам об этом по почте. Данную вкладку можно закрыть.</div>');
    $.ajax({
        type: 'GET',
        url: '/room/check_roots',
        data: {},
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                $(".errors").append('<div class="alert alert-success" id="error_output" role="alert">Источники успешно проверены</div>');
            } else if (data == 'no_roots') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">У вас не найдено ни одного источника</div>');
            } else if (data == 'bad') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При проверке источников возникла ошибка, повторите попытку</div>');
            } else if (data == 'many_requests') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Проверку источников можно делать только раз в 5 минут!</div>');
            }
        }
    });
})