$('#send_new_message').click(function () {
    body = $('#body-message').val();
    if (body.length < 1) {
        $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При отправке сообщения возникла ошибка</div>');
        return (null)
    }
    id_vk_acc = $(this).attr('data-id-vk-acc');
    id_dialog = $(this).attr('data-id-dialog');
    $.ajax({
        type: 'GET',
        url: '/room/send_message',
        data: {
            'body':body,
            'id_vk_acc':id_vk_acc,
            'id_dialog':id_dialog,
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При отправке сообщения возникла ошибка</div>');
            }
        }
    });
});