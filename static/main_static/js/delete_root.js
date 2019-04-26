
$('.delete_group').click(function () {
    gid = $(this).attr('data-gid');
    group_del = $('#'+gid);
    group_del.toggle('normal');
    $.ajax({
        type: 'GET',
        url: '/room/delete_group/'+gid,
        data: {},
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При удалении источника возникла ошибка</div>');
            }
        }
    });
});