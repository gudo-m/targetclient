$(document).ready(function() {
    var windowWidth = $(window).width();
    if(windowWidth < 992) {
        $(".client-cl").removeClass("d-flex align-items-center");
    }
    $(window).resize(function(){
        var windowWidth = $(window).width();
        if(windowWidth < 992) {
            $(".client-cl").removeClass("d-flex align-items-center");
        } else {
            $(".client-cl").addClass("d-flex align-items-center");
        }
  });
});


$('.select_client').click(function () {
    c_id = $(this).attr('data-gid');
    $.ajax({
        type: 'GET',
        url: '/room/select_client',
        data: {
            'c_id':c_id,
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При выборе источника возникла ошибка</div>');
            }
        }
    });
});