
$('.delete_vk_account').click(function () {
    gid = $(this).attr('data-uid');
    $.ajax({
        type: 'GET',
        url: '/room/delete_vk_account',
        data: {
            'acc_id': gid,
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else if (data == 'bad') {
                 $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При удалении аккаунта возникла ошибка</div>');
            }
        }
    });
})