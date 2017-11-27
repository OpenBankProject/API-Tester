$(function() {
	function escapeHTML(s) {
		return String(s).replace(/&(?!\w+;)/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
	}

	function runTest(runner) {
		var testpath = runner.data('testpath');
		$.get(testpath, function (data) {
			var alertType = 'success';
			var msg = '';
			var collapse = '';
			var text = `<pre>${escapeHTML(data['text'])}</pre>`;
			if (!data['success']) {
				alertType = 'danger';
				msg = '<ul>';
				for (var i=0; i < data['messages'].length; i++) {
					msg += `<li>${data['messages'][i]}</li>`;
				}
				msg += '</ul>';
			} else {
				collapse = `<button type="button" class="btn btn-xs btn-success pull-right" data-toggle="collapse" data-target="#${data['config']['operation_id']}"><span class="glyphicon glyphicon-chevron-down"></span></button>`;
				text = `<div id="${data['config']['operation_id']}" class="collapse">${text}</div>`;
			}
			var result = `<div class="alert alert-${alertType}"><div class="row"><div class="col-xs-10 col-sm-11">${data['config']['summary']}<br />${data['config']['urlpath']}<br />Took ${data['execution_time']} ms<br />${msg}</div><div class="col-xs-2 col-sm-1">${collapse}</div></div>${text}</div>`;
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
