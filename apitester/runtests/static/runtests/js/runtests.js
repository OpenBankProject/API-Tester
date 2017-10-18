$(function() {
	function runTest(runner) {
		var testpath = runner.data('testpath');
		$.get(testpath, function (data) {
            var alertType = 'success';
            var msg = '';
			if (!data['success']) {
                alertType = 'danger';
				msg = '<ul>';
				for (var i=0; i < data['messages'].length; i++) {
					msg += `<li>${data['messages'][i]}</li>`;
				}
				msg += '</ul>';
			}
			var result = `<div class="alert alert-${alertType}">${data['config']['summary']}<br />${data['config']['urlpath']}<br />${msg}<br /><pre>${data['text']}</pre><br />Took ${data['execution_time']} ms</div>`;
			$(runner.find('.result')).append(result);
		});
	}

	$('#run').click(function() {
		$('.result').empty();
		var runners = $('.runner');
		for (var i=0; i < runners.length; i++) {
			var runner = $(runners[i]);
			if (runner.find('input').is(':checked')) {
				runTest(runner);
			}
		}
	});
	$('.runner button').click(function() {
		var runner = $(this).parent().parent().parent();
		$(runner).find('.result').empty();
		runTest(runner);
	});

	$('#checkNone').click(function() {
		$('.runner').find('input').prop('checked', false);
	});
	$('#checkAll').click(function() {
		$('.runner').find('input').prop('checked', true);
	});

    $('#select-testconfig').change(function() {
        var configPk = $(this).val();
        if (configPk) {
            location.href = `${URL_RUNTESTS_INDEX}${configPk}`;
        } else  {
            location.href = URL_RUNTESTS_INDEX;
        }
    })

    var configPk = location.href.substr(location.href.lastIndexOf('/') + 1);
    if (configPk) {
        $('#nothing-selected').addClass('hide');
        $('#select-testconfig').val(configPk);
        $('#run-buttons').removeClass('hide');
        $('#test-list').removeClass('hide');
    }
});
