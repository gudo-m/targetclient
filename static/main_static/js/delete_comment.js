$(document).ready(function() {
    var windowWidth = $(window).width();
    if(windowWidth < 992) {
        $(".cl-comments").removeClass("d-flex align-items-center");
    }
    $(window).resize(function(){
        var windowWidth = $(window).width();
        if(windowWidth < 992) {
            $(".cl-comments").removeClass("d-flex align-items-center");
        } else {
            $(".cl-comments").addClass("d-flex align-items-center");
        }
  });
});


$('.delete_comment').click(function () {
    gid = $(this).attr('data-gid');
    uid = $(this).attr('data-uid');
    card_now = $('#'+gid+'-'+uid);
    card_now.toggle('normal');
    $.ajax({
        type: 'GET',
        url: '/room/delete_comment',
        data: {
            'cid':$(this).attr('data-cid'),
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При удалении комментария возникла ошибка</div>');
            }
        }
    });
});