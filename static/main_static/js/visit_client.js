$('.visit_client').click(function () {
    c_id = $(this).attr('data-cid');
    $.ajax({
        type: 'GET',
        url: '/room/visit_client',
        data: {
            'c_id':c_id,
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                var p_comment = $('*[data-for-search="'+c_id+'"]');
                p_comment.removeClass('text-black-50');
                p_comment.addClass('visited-client');
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Возникла неизвестная ошибка</div>');
            }
        }
    });
});