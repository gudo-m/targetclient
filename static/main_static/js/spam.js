
$('#start_spam').click(function () {
    $("#exampleModal2").modal('hide');
    val_select = $('#inputGroupSelect01').val();
    val_text = $('#text_message').val();
    val_range_or_diap = $('#flag').attr('data-now-active');
    val_range = $('#r1').val();
    spam_last = $('#spam_last')[0].checked;
    val_range_from = $('#r2').val();
    val_range_to = $('#r3').val();
    $(".errors").append('<div class="alert alert-info" id="error_output" role="alert">Рассылка сообщений началась! По завершению мы вам отправим письмо на почту.</div>');
    $.ajax({
        type: 'GET',
        url: '/room/start_spam',
        data: {
           'selected': val_select,
           'text': val_text,
           'ranged': val_range,
           'ranged_from': val_range_from,
           'ranged_to': val_range_to,
            'ranged_or_diap': val_range_or_diap,
            'spam_last': spam_last,
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                $(".errors").append('<div class="alert alert-success" id="error_output" role="alert">Рассылка сообщений успешно завершена</div>');
            } else if (data == 'bad') {
                 $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При рассылке сообщений возникла ошибка</div>');
            } else if (data == 'many_requests') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Рассылку сообщений можно делать только раз в 5 минут!</div>');
            }
        }
    });
})