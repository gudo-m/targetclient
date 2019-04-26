$(document).ready(function() {
    var windowWidth = $(window).width();
    if(windowWidth < 992) {
        $(".group-cl").removeClass("d-flex align-items-center");
    }
    $(window).resize(function(){
        var windowWidth = $(window).width();
        if(windowWidth < 992) {
            $(".group-cl").removeClass("d-flex align-items-center");
        } else {
            $(".group-cl").addClass("d-flex align-items-center");
        }
  });
});


$('#add_group').click(function () {
    $("#exampleModal").modal('hide');
    $(".errors").append('<div class="alert alert-info" id="error_output" role="alert">Ваша группа добавится в список через некоторое время, мы сообщим вам об этом по почте. Данную вкладку можно закрыть.</div>');
    $.ajax({
        type: 'GET',
        url: '/room/add_group',
        data: {
           'group_id': $('#group_id').val(),
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'started') {
                $(".errors").append('<div class="alert alert-success" id="error_output" role="alert">Добавление источника успешно началось!</div>');
            } else if (data == 'bad') {
                 $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При добавлении источника возникла ошибка!</div>');
            } else if (data == 'many_requests') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">За одну минуту можно добавлять источники только один раз!</div>');
            } else if (data == 'too_many_groups') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Вы добавили максимальное количество источников (ограничение идёт по тарифам)!</div>');
            } else if (data == 'too_big') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Размер источника слишком большой (ограничение по тарифу)!</div>');
            }
        }
    });
})