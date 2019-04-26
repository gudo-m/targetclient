
$('.delete_client').click(function () {
    uid = $(this).attr('data-uid');
    gid = $(this).attr('data-gid');
    card_now = $('#'+gid+'-'+uid);
    card_now.toggle('normal');
    $.ajax({
        type: 'GET',
        url: '/room/delete_client/'+uid,
        data: {
            'gr_id':gid,
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При удалении клиента возникла ошибка</div>');
            }
        }
    });
});