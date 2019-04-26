$('#delete_dialog').click(function () {
    id_vk_acc = $(this).attr('data-id-vk-acc');
    id_dialog = $(this).attr('data-id-dialog');
    $('#exampleModal').modal('hide');
    $.ajax({
        type: 'GET',
        url: '/room/delete_dialog',
        data: {
            'id_vk_acc':id_vk_acc,
            'id_dialog':id_dialog,
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                window.open("http://www.targetclient.tk/room/dialogs/"+id_vk_acc,"_self")
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При удалении диалога возникла ошибка</div>');
            }
        }
    });
});