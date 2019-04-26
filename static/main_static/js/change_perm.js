$('#change_perm').click(function () {
    select_plan = $('#select-plan').val();
    $("#exampleModal").modal('hide');
    $.ajax({
        type: 'GET',
        url: '/room/change_perm',
        data: {
            'selected': select_plan,
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else if (data == 'many_requests') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Изменять тариф можно только раз в 10 дней</div>');
            } else if (data == 'admin') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Администраторы не могут изменять свой тариф!</div>');
            } else if (data == 'no_money') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Недостаточно средств на балансе аккаунта!</div>');
            } else {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При изменении тарифа возникла ошибка</div>');
            }
        }
    });
});