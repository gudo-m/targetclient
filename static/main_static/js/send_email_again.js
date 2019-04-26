$('#basic-addon3').click(function () {
    $.ajax({
        type: 'GET',
        url: '/accounts/send_email_again',
        data: {},
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                $(".errors").append('<div class="alert alert-success" id="error_output" role="alert">Письмо успешно отправлено. Если не можете найти письмо, обязательно проверьте папку "СПАМ"!</div>');
            } else if (data == 'many_requests') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">За день можно отправить только одно повторное письмо</div>');
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При отправке письма возникла ошибка</div>');
            }
        }
    });
});