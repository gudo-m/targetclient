$('#confirm_promocode').click(function () {
    $.ajax({
        type: 'GET',
        url: '/accounts/confirm_promocode/',
        data: {
            'promoc':$('#promocode_conf').val(),
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При подтверждении промокода возникла ошибка</div>');
            }
        }
    });
});