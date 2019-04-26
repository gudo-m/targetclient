
$('#add_account').click(function () {
    $("#exampleModal").modal('hide');
    $.ajax({
        type: 'GET',
        url: '/room/add_vk_account',
        data: {
           'ulogin': $('#add_logn').val(),
           'upassword': $('#add_passwd').val(),
        },
        dataType: 'text',
        cache: false,

        success: function (data) {
            if (data == 'ok') {
                location.reload();
            } else if (data == 'bad') {
                 $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">При добавлении аккаунта возникла ошибка, проверьте логин и пароль</div>');
            } else if (data == 'blocked') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Ошибка. Данный аккаунт заблокирован</div>');
            } else if (data == 'exists') {
                $(".errors").append('<div class="alert alert-danger" id="error_output" role="alert">Ошибка. Данный аккаунт уже добавлен</div>');
            }
        }
    });
})