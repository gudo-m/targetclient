$('.select_comment').click(function () {
    $.ajax({
        type: 'GET',
        url: '/room/select_comment',
        data: {
            'cid':$(this).attr('data-cid'),
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При выборе комментария возникла ошибка</div>');
            }
        }
    });
});